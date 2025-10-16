"""
Unified AceStream Proxy Service
Based on pyacexy with enhancements
"""
import asyncio
import logging
import uuid
from typing import Optional, Dict, Set
from urllib.parse import urlencode
from datetime import datetime

import aiohttp
from aiohttp import web, ClientSession

logger = logging.getLogger(__name__)


class AceStreamInfo:
    """AceStream session information"""
    
    def __init__(self, playback_url: str, stat_url: str, command_url: str, stream_id: str):
        self.playback_url = playback_url
        self.stat_url = stat_url
        self.command_url = command_url
        self.stream_id = stream_id


class OngoingStream:
    """Represents an ongoing stream with multiple clients"""
    
    def __init__(self, stream_id: str, acestream: AceStreamInfo):
        self.stream_id = stream_id
        self.acestream = acestream
        self.clients: Dict[str, asyncio.Queue] = {}  # client_id -> their own queue
        self.lock = asyncio.Lock()
        self.done = asyncio.Event()
        self.started = asyncio.Event()
        self.first_chunk = asyncio.Event()
        self.fetch_task: Optional[asyncio.Task] = None
        self.created_at = datetime.utcnow()
        self.client_last_active: Dict[str, float] = {}  # Track client activity
        

class AceProxyService:
    """AceStream Proxy Service with multiplexing support"""
    
    def __init__(
        self,
        acestream_host: str = "localhost",
        acestream_port: int = 6878,
        buffer_size: int = 5 * 1024 * 1024,
        timeout: int = 15,
        chunk_size: int = 32768,  # 32KB chunks (vs 8KB) - fewer operations
    ):
        self.acestream_host = acestream_host
        self.acestream_port = acestream_port
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.base_url = f"http://{acestream_host}:{acestream_port}"
        
        self.streams: Dict[str, OngoingStream] = {}
        self.streams_lock = asyncio.Lock()
        self.session: Optional[ClientSession] = None
        
    async def start(self):
        """Start the proxy service"""
        self.session = ClientSession()
        logger.info(f"AceProxy service started - connecting to {self.base_url}")
        
    async def stop(self):
        """Stop the proxy service"""
        if self.session:
            await self.session.close()
        
        # Close all ongoing streams
        async with self.streams_lock:
            for stream in list(self.streams.values()):
                await self._close_stream(stream)
        
        logger.info("AceProxy service stopped")
    
    async def _fetch_stream_info(self, stream_id: str) -> AceStreamInfo:
        """Fetch stream information from AceStream engine"""
        temp_pid = str(uuid.uuid4())
        
        url = f"{self.base_url}/ace/getstream"
        params = {
            'id': stream_id,
            'format': 'json',
            'pid': temp_pid
        }
        
        logger.debug(f"Fetching stream info for {stream_id}")
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        try:
            async with self.session.get(url, params=params, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"AceStream returned {response.status}: {error_text}")
                
                data = await response.json()
                
                if 'error' in data and data['error']:
                    raise Exception(f"AceStream error: {data['error']}")
                
                if 'response' not in data:
                    raise Exception("Invalid response from AceStream")
                
                resp = data['response']
                
                return AceStreamInfo(
                    playback_url=resp['playback_url'],
                    stat_url=resp.get('stat_url', ''),
                    command_url=resp['command_url'],
                    stream_id=stream_id
                )
        except asyncio.TimeoutError:
            raise Exception(f"Timeout fetching stream info for {stream_id}")
        except Exception as e:
            logger.error(f"Error fetching stream info: {e}")
            raise
    
    async def _close_stream(self, ongoing: OngoingStream):
        """Close stream on AceStream engine"""
        try:
            url = f"{ongoing.acestream.command_url}?method=stop"
            logger.debug(f"Closing stream {ongoing.stream_id}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'error' in data and data['error']:
                        logger.warning(f"Error closing stream: {data['error']}")
                        
            ongoing.done.set()
            
            if ongoing.fetch_task and not ongoing.fetch_task.done():
                ongoing.fetch_task.cancel()
                
        except Exception as e:
            logger.warning(f"Exception closing stream: {e}")
    
    async def _fetch_acestream(self, ongoing: OngoingStream):
        """Fetch stream from AceStream and distribute to all clients (like pyacexy)"""
        logger.info(f"Starting fetch for stream {ongoing.stream_id}")
        
        # Use sock_read timeout (like pyacexy - empty_timeout)
        timeout = aiohttp.ClientTimeout(sock_read=60)
        
        try:
            async with self.session.get(ongoing.acestream.playback_url, timeout=timeout) as ace_response:
                if ace_response.status != 200:
                    logger.error(f"AceStream returned {ace_response.status}")
                    ongoing.started.set()
                    return
                
                # Signal connection established (like pyacexy)
                ongoing.started.set()
                logger.info(f"Stream {ongoing.stream_id} started successfully")
                
                # Read chunks and distribute to ALL clients (like pyacexy _start_acestream_fetch)
                chunk_count = 0
                last_cleanup = asyncio.get_event_loop().time()
                
                async for chunk in ace_response.content.iter_chunked(self.chunk_size):
                    if ongoing.done.is_set():
                        break
                    
                    chunk_count += 1
                    current_time = asyncio.get_event_loop().time()
                    
                    # Periodically cleanup stale clients (every 15 seconds, like pyacexy)
                    if current_time - last_cleanup > 15:
                        last_cleanup = current_time
                        await self._cleanup_stale_clients(ongoing, current_time)
                    
                    # Get snapshot of clients (quick, inside lock)
                    async with ongoing.lock:
                        clients_snapshot = list(ongoing.clients.items())
                    
                    # Distribute to clients (outside lock for better concurrency)
                    dead_clients = []
                    tasks = []
                    
                    for client_id, client_queue in clients_snapshot:
                        # Create task for each client (non-blocking distribution)
                        task = asyncio.create_task(
                            self._send_to_client(chunk, client_id, client_queue, current_time, ongoing, chunk_count)
                        )
                        tasks.append((client_id, task))
                    
                    # Wait for all sends to complete (with timeout)
                    for client_id, task in tasks:
                        try:
                            result = await asyncio.wait_for(task, timeout=0.15)
                            if not result:
                                dead_clients.append(client_id)
                        except asyncio.TimeoutError:
                            # Client too slow
                            dead_clients.append(client_id)
                        except Exception as e:
                            logger.warning(f"Error in send task for {client_id}: {e}")
                            dead_clients.append(client_id)
                        
                        # Remove dead clients
                        if dead_clients:
                            for client_id in dead_clients:
                                ongoing.clients.pop(client_id, None)
                                ongoing.client_last_active.pop(client_id, None)
                            logger.info(f"Removed {len(dead_clients)} dead clients from {ongoing.stream_id}")
                        
                        # If no clients left, stop
                        if not ongoing.clients:
                            logger.info(f"No clients left for stream {ongoing.stream_id}, stopping")
                            break
                        
        except asyncio.TimeoutError:
            logger.info(f"Stream {ongoing.stream_id} timed out (no data for 60s)")
            ongoing.started.set()
        except asyncio.CancelledError:
            logger.info(f"Stream {ongoing.stream_id} fetch cancelled")
        except Exception as e:
            logger.error(f"Error fetching stream {ongoing.stream_id}: {e}")
        finally:
            ongoing.done.set()
            logger.info(f"Stream {ongoing.stream_id} fetch completed")
    
    async def _cleanup_stale_clients(self, ongoing: OngoingStream, current_time: float):
        """Remove clients that haven't been active (like pyacexy stale cleanup)"""
        stale_clients = []
        
        for client_id, last_active in ongoing.client_last_active.items():
            # If client hasn't been active in 30 seconds, consider it stale
            if current_time - last_active > 30:
                logger.warning(f"Client {client_id} inactive for {current_time - last_active:.0f}s, removing")
                stale_clients.append(client_id)
        
        if stale_clients:
            for client_id in stale_clients:
                ongoing.clients.pop(client_id, None)
                ongoing.client_last_active.pop(client_id, None)
            logger.info(f"Removed {len(stale_clients)} stale clients from {ongoing.stream_id}")
    
    async def _send_to_client(
        self, 
        chunk: bytes, 
        client_id: str, 
        client_queue: asyncio.Queue,
        current_time: float,
        ongoing: OngoingStream,
        chunk_count: int
    ) -> bool:
        """Send chunk to a single client (helper for parallel distribution)"""
        try:
            # Try non-blocking first
            try:
                client_queue.put_nowait(chunk)
                ongoing.client_last_active[client_id] = current_time
                if chunk_count == 1:
                    ongoing.first_chunk.set()
                return True
            except asyncio.QueueFull:
                # Queue full - wait with timeout
                try:
                    await asyncio.wait_for(client_queue.put(chunk), timeout=0.1)
                    ongoing.client_last_active[client_id] = current_time
                    return True
                except asyncio.TimeoutError:
                    # Client too slow
                    return False
        except Exception as e:
            logger.debug(f"Error sending to client {client_id}: {e}")
            return False
    
    async def get_stream(self, stream_id: str, client_id: str) -> asyncio.Queue:
        """Get or create stream for client"""
        async with self.streams_lock:
            # Check if stream already exists
            if stream_id in self.streams:
                ongoing = self.streams[stream_id]
                ongoing.clients.add(client_id)
                logger.info(f"Client {client_id} joined existing stream {stream_id} ({len(ongoing.clients)} clients)")
                return ongoing.buffer
            
            # Create new stream
            logger.info(f"Creating new stream for {stream_id}")
            acestream_info = await self._fetch_stream_info(stream_id)
            
            ongoing = OngoingStream(stream_id, acestream_info)
            ongoing.clients.add(client_id)
            
            # Start fetching
            ongoing.fetch_task = asyncio.create_task(self._fetch_acestream(ongoing))
            
            self.streams[stream_id] = ongoing
            
            # Wait for stream to start
            await asyncio.wait_for(ongoing.started.wait(), timeout=self.timeout)
            
            return ongoing.buffer
    
    async def remove_client(self, stream_id: str, client_id: str):
        """Remove client from stream"""
        async with self.streams_lock:
            if stream_id not in self.streams:
                return
            
            ongoing = self.streams[stream_id]
            ongoing.clients.discard(client_id)
            
            logger.info(f"Client {client_id} left stream {stream_id} ({len(ongoing.clients)} clients remaining)")
            
            # If no clients left, close stream
            if not ongoing.clients:
                logger.info(f"No clients left for stream {stream_id}, closing")
                await self._close_stream(ongoing)
                del self.streams[stream_id]
    
    async def get_stream_stats(self, stream_id: str) -> Optional[dict]:
        """Get statistics for a stream"""
        # Get ongoing stream reference without holding lock for I/O
        async with self.streams_lock:
            if stream_id not in self.streams:
                return None
            ongoing = self.streams[stream_id]
        
        # Get stats from AceStream without holding global lock
        try:
            if ongoing.acestream.stat_url:
                async with self.session.get(ongoing.acestream.stat_url) as response:
                    if response.status == 200:
                        ace_stats = await response.json()
                    else:
                        ace_stats = {}
            else:
                ace_stats = {}
        except Exception as e:
            logger.warning(f"Error getting stream stats: {e}")
            ace_stats = {}
        
        return {
            'stream_id': stream_id,
            'clients': len(ongoing.clients),
            'total_queue_size': sum(q.qsize() for q in ongoing.clients.values()),
            'created_at': ongoing.created_at.isoformat(),
            'acestream_stats': ace_stats
        }
    
    async def get_all_streams(self) -> list:
        """Get all active streams"""
        # Get snapshot of stream IDs without holding lock during stats collection
        async with self.streams_lock:
            stream_ids = list(self.streams.keys())
        
        # Collect stats without holding global lock
        result = []
        for stream_id in stream_ids:
            stats = await self.get_stream_stats(stream_id)
            if stats:
                result.append(stats)
        return result
    
    async def check_stream_available(self, stream_id: str) -> bool:
        """Check if a stream is available"""
        try:
            await self._fetch_stream_info(stream_id)
            return True
        except Exception as e:
            logger.debug(f"Stream {stream_id} not available: {e}")
            return False
    
    async def stream_content(self, stream_id: str):
        """Stream content from AceStream (generator for FastAPI StreamingResponse)"""
        # Check if stream exists first
        ongoing = None
        
        async with self.streams_lock:
            if stream_id in self.streams:
                ongoing = self.streams[stream_id]
        
        # Create new stream if needed
        if ongoing is None:
            logger.info(f"Creating new stream for {stream_id}")
            
            # Fetch stream info
            acestream_info = await self._fetch_stream_info(stream_id)
            
            # Create stream
            async with self.streams_lock:
                # Check again in case another client created it
                if stream_id in self.streams:
                    ongoing = self.streams[stream_id]
                else:
                    ongoing = OngoingStream(stream_id, acestream_info)
                    self.streams[stream_id] = ongoing
                    
                    # Start fetching
                    ongoing.fetch_task = asyncio.create_task(self._fetch_acestream(ongoing))
            
            # Wait for stream to start
            await asyncio.wait_for(ongoing.started.wait(), timeout=self.timeout)
        
        # Create client queue (each client has its own queue)
        # With 32KB chunks, 50 elements = ~1.6MB buffer (same as before with 100x8KB)
        client_id = str(uuid.uuid4())
        client_queue = asyncio.Queue(maxsize=50)
        
        async with ongoing.lock:
            ongoing.clients[client_id] = client_queue
            ongoing.client_last_active[client_id] = asyncio.get_event_loop().time()
            client_count = len(ongoing.clients)
        
        logger.info(f"Client {client_id} streaming {stream_id} ({client_count} clients)")
        
        try:
            # Stream chunks from client's own queue
            chunk_count = 0
            while not ongoing.done.is_set():
                try:
                    # Get chunk from this client's queue (blocking with timeout)
                    chunk = await asyncio.wait_for(client_queue.get(), timeout=2.0)
                    yield chunk
                    chunk_count += 1
                    # Update activity periodically (every 50 chunks to reduce overhead)
                    if chunk_count % 50 == 0:
                        ongoing.client_last_active[client_id] = asyncio.get_event_loop().time()
                except asyncio.TimeoutError:
                    # Check if stream is still active
                    if ongoing.done.is_set():
                        break
                    continue
                except Exception as e:
                    logger.warning(f"Error getting chunk for client {client_id}: {e}")
                    break
        finally:
            # Remove client
            async with ongoing.lock:
                ongoing.clients.pop(client_id, None)
                ongoing.client_last_active.pop(client_id, None)
                remaining = len(ongoing.clients)
            
            logger.info(f"Client {client_id} disconnected from {stream_id} ({remaining} clients remaining)")
            
            # Close stream if no clients
            if remaining == 0:
                asyncio.create_task(self._cleanup_stream(stream_id, ongoing))
    
    async def _cleanup_stream(self, stream_id: str, ongoing: OngoingStream):
        """Cleanup stream without clients (called as background task)"""
        async with self.streams_lock:
            # Double-check no clients joined in the meantime
            if stream_id in self.streams and len(ongoing.clients) == 0:
                logger.info(f"No clients left for {stream_id}, closing")
                await self._close_stream(ongoing)
                del self.streams[stream_id]
    
    async def close_stream(self, stream_id: str):
        """Force close a stream"""
        async with self.streams_lock:
            if stream_id in self.streams:
                ongoing = self.streams[stream_id]
                await self._close_stream(ongoing)
                del self.streams[stream_id]
                logger.info(f"Forcibly closed stream {stream_id}")
