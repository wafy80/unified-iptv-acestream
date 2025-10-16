"""
AceStream Streaming Server using aiohttp with pyacexy native pattern
This server runs on a separate port and handles streaming with direct write (no queues)
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Set, NamedTuple
from urllib.parse import urlencode

import aiohttp
from aiohttp import web, ClientSession

logger = logging.getLogger(__name__)


class ClientInfo(NamedTuple):
    """Client connection information"""
    ip: str
    user_agent: str
    username: str
    connected_at: datetime
    response: web.StreamResponse


class AceStreamInfo:
    """AceStream session information"""
    
    def __init__(self, playback_url: str, stat_url: str, command_url: str, stream_id: str):
        self.playback_url = playback_url
        self.stat_url = stat_url
        self.command_url = command_url
        self.stream_id = stream_id


class OngoingStream:
    """Represents an ongoing stream with multiple clients (pyacexy pattern)"""
    
    def __init__(self, stream_id: str, acestream: AceStreamInfo):
        self.stream_id = stream_id
        self.acestream = acestream
        self.clients: Dict[int, ClientInfo] = {}  # Map response ID to ClientInfo
        self.lock = asyncio.Lock()
        self.done = asyncio.Event()
        self.started = asyncio.Event()
        self.first_chunk = asyncio.Event()
        self.fetch_task: Optional[asyncio.Task] = None
        self.client_last_write: Dict[int, float] = {}  # Track last successful write per client
        self.created_at = datetime.now()  # Track when stream was created


class AiohttpStreamingServer:
    """
    AceStream HTTP Streaming Server using aiohttp
    Native pyacexy pattern: direct write to StreamResponse (no queues, no tasks)
    """
    
    def __init__(
        self,
        acestream_host: str = "localhost",
        acestream_port: int = 6878,
        listen_host: str = "127.0.0.1",
        listen_port: int = 8001,
        scheme: str = "http",
        chunk_size: int = 8192,  # 8KB like pyacexy
        empty_timeout: float = 60.0,
        no_response_timeout: float = 10.0,
    ):
        self.acestream_host = acestream_host
        self.acestream_port = acestream_port
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.scheme = scheme
        self.chunk_size = chunk_size
        self.empty_timeout = empty_timeout
        self.no_response_timeout = no_response_timeout
        self.endpoint = "/ace/getstream"
        
        self.streams: Dict[str, OngoingStream] = {}
        self.streams_lock = asyncio.Lock()
        self.session: Optional[ClientSession] = None
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
    
    async def _fetch_stream_info(self, stream_id: str, extra_params: dict) -> AceStreamInfo:
        """Fetch stream information from AceStream engine"""
        temp_pid = str(uuid.uuid4())
        
        url = f"{self.scheme}://{self.acestream_host}:{self.acestream_port}{self.endpoint}"
        
        params = extra_params.copy()
        params['format'] = 'json'
        params['pid'] = temp_pid
        params['id'] = stream_id
        
        logger.debug(f"Fetching stream info: {url}?{urlencode(params)}")
        
        timeout = aiohttp.ClientTimeout(total=self.no_response_timeout)
        
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
    
    async def _close_stream(self, acestream: AceStreamInfo):
        """Close stream on AceStream engine"""
        try:
            url = f"{acestream.command_url}?method=stop"
            logger.debug(f"Closing stream: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'error' in data and data['error']:
                        logger.warning(f"Error closing stream: {data['error']}")
                else:
                    logger.warning(f"Failed to close stream, status: {response.status}")
        except Exception as e:
            logger.warning(f"Exception while closing stream: {e}")
    
    async def _fetch_acestream(self, ongoing: OngoingStream):
        """
        Fetch stream from AceStream and distribute to all clients
        NATIVE PYACEXY PATTERN: Direct write to StreamResponse (no queues)
        """
        logger.info(f"Starting AceStream fetch for {ongoing.stream_id}")
        
        # sock_read timeout (like pyacexy)
        timeout = aiohttp.ClientTimeout(sock_read=self.empty_timeout)
        
        try:
            logger.debug(f"Connecting to AceStream: {ongoing.acestream.playback_url}")
            async with self.session.get(ongoing.acestream.playback_url, timeout=timeout) as ace_response:
                logger.debug(f"AceStream response status: {ace_response.status}")
                if ace_response.status != 200:
                    logger.error(f"AceStream returned status {ace_response.status}")
                    ongoing.started.set()
                    return
                
                # Signal connection established (like pyacexy)
                ongoing.started.set()
                logger.info(f"Stream {ongoing.stream_id} connected, reading chunks")
                
                # Read chunks and distribute to ALL clients (PYACEXY PATTERN)
                chunk_count = 0
                last_cleanup = asyncio.get_event_loop().time()
                
                async for chunk in ace_response.content.iter_chunked(self.chunk_size):
                    if not chunk:
                        break
                    
                    chunk_count += 1
                    if chunk_count % 100 == 0:
                        logger.debug(f"Stream {ongoing.stream_id} sent {chunk_count} chunks")
                    
                    # Periodic stale client cleanup (every 15 seconds, like pyacexy)
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_cleanup > 15:
                        last_cleanup = current_time
                        async with ongoing.lock:
                            stale_client_ids = []
                            for client_id, client_info in list(ongoing.clients.items()):
                                last_write = ongoing.client_last_write.get(client_id, 0)
                                # Inactive for 30 seconds = stale
                                if current_time - last_write > 30:
                                    logger.warning(f"Client {client_info.ip} inactive for {current_time - last_write:.0f}s, removing")
                                    stale_client_ids.append(client_id)
                            
                            for client_id in stale_client_ids:
                                client_info = ongoing.clients.pop(client_id, None)
                                ongoing.client_last_write.pop(client_id, None)
                                if client_info:
                                    try:
                                        await client_info.response.write_eof()
                                    except:
                                        pass
                            
                            if stale_client_ids:
                                logger.info(f"Removed {len(stale_client_ids)} stale client(s)")
                    
                    # DIRECT WRITE TO ALL CLIENTS (PYACEXY NATIVE PATTERN - NO QUEUES!)
                    async with ongoing.lock:
                        dead_client_ids = []
                        current_time = asyncio.get_event_loop().time()
                        
                        for client_id, client_info in list(ongoing.clients.items()):
                            try:
                                # Direct write (like pyacexy: await client_response.write(chunk))
                                await client_info.response.write(chunk)
                                # Track successful write
                                ongoing.client_last_write[client_id] = current_time
                                # Signal first chunk
                                if chunk_count == 1:
                                    ongoing.first_chunk.set()
                            except Exception as e:
                                logger.warning(f"Error writing to client {client_info.ip}: {e}")
                                dead_client_ids.append(client_id)
                        
                        # Remove dead clients
                        if dead_client_ids:
                            for client_id in dead_client_ids:
                                client_info = ongoing.clients.pop(client_id, None)
                                ongoing.client_last_write.pop(client_id, None)
                                if client_info:
                                    try:
                                        await client_info.response.write_eof()
                                    except:
                                        pass
                            client_count = len(ongoing.clients)
                            logger.info(f"Removed {len(dead_client_ids)} dead client(s), {client_count} remaining")
                        
                        # Stop if no clients left
                        if not ongoing.clients:
                            logger.info(f"No clients left for stream {ongoing.stream_id}, stopping")
                            break
                            
        except asyncio.TimeoutError:
            logger.info(f"Stream {ongoing.stream_id} timed out (no data for {self.empty_timeout}s)")
            ongoing.started.set()
        except Exception as e:
            logger.error(f"Error fetching AceStream: {e}")
            ongoing.started.set()
        finally:
            # Clean up all remaining clients
            async with ongoing.lock:
                for client_info in list(ongoing.clients.values()):
                    try:
                        await client_info.response.write_eof()
                    except:
                        pass
                ongoing.clients.clear()
            
            # Close the stream
            await self._close_stream(ongoing.acestream)
            
            # Signal done
            ongoing.done.set()
            
            # Remove from active streams
            async with self.streams_lock:
                if ongoing.stream_id in self.streams:
                    del self.streams[ongoing.stream_id]
                    logger.info(f"Stream {ongoing.stream_id} cleaned up")
    
    async def handle_getstream(self, request: web.Request) -> web.StreamResponse:
        """
        Handle /ace/getstream endpoint
        NATIVE PYACEXY PATTERN
        """
        # Get stream ID from query
        stream_id = request.query.get('id', '')
        infohash = request.query.get('infohash', '')
        username = request.query.get('username', 'Anonymous')
        # Get REAL client info passed from Xtream API
        client_ip = request.query.get('client_ip', request.remote)  # Fallback to proxy IP
        client_ua = request.query.get('client_ua', request.headers.get('User-Agent', 'Unknown'))
        
        if not stream_id and not infohash:
            return web.Response(status=400, text="Missing id or infohash parameter")
        
        if stream_id and infohash:
            return web.Response(status=400, text="Only one of id or infohash can be specified")
        
        if 'pid' in request.query:
            return web.Response(status=400, text="PID parameter is not allowed")
        
        key = stream_id or infohash
        
        logger.info(f"Client {client_ip} (user: {username}) requesting stream {key} (UA: {client_ua})")
        
        # Get extra parameters (exclude username, id, infohash, pid, client_ip, client_ua)
        extra_params = {k: v for k, v in request.query.items() 
                       if k not in ('id', 'infohash', 'pid', 'username', 'client_ip', 'client_ua')}
        
        # Get or create ongoing stream
        async with self.streams_lock:
            if key not in self.streams:
                logger.info(f"Creating new stream for {key}")
                try:
                    acestream = await self._fetch_stream_info(key, extra_params)
                    ongoing = OngoingStream(key, acestream)
                    self.streams[key] = ongoing
                except Exception as e:
                    logger.error(f"Failed to fetch stream info: {e}")
                    return web.Response(status=500, text=f"Failed to start stream: {e}")
            else:
                logger.info(f"Reusing existing stream for {key}")
                ongoing = self.streams[key]
        
        # Create response for this client
        response = web.StreamResponse()
        response.content_type = 'video/MP2T'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        # Prepare response FIRST (before adding to clients)
        await response.prepare(request)
        
        # Add client and start stream if needed (PYACEXY PATTERN)
        need_to_wait = False
        async with ongoing.lock:
            # Create client info with REAL client data (not proxy data)
            client_info = ClientInfo(
                ip=client_ip,  # Real client IP from Xtream API
                user_agent=client_ua,  # Real User-Agent from Xtream API
                username=username,
                connected_at=datetime.now(),
                response=response
            )
            # Add client to list with ClientInfo
            response_id = id(response)
            ongoing.clients[response_id] = client_info
            client_count = len(ongoing.clients)
            logger.info(f"Stream {key} now has {client_count} client(s)")
            
            # Check if stream is already active
            if ongoing.fetch_task is None or ongoing.fetch_task.done():
                # Start stream
                need_to_wait = True
                ongoing.fetch_task = asyncio.create_task(self._fetch_acestream(ongoing))
        
        # If we just started, wait for first chunk
        if need_to_wait:
            try:
                await asyncio.wait_for(ongoing.started.wait(), timeout=10.0)
                await asyncio.wait_for(ongoing.first_chunk.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for stream {key} to start")
                async with ongoing.lock:
                    ongoing.clients.pop(response_id, None)
                return web.Response(status=503, text="Stream failed to start")
        
        try:
            # Wait for stream to finish (client disconnect handled by write errors)
            await ongoing.done.wait()
            logger.debug(f"Stream finished for {key}")
        except Exception as e:
            logger.debug(f"Client exception: {e}")
        finally:
            # Remove this client
            async with ongoing.lock:
                was_present = response_id in ongoing.clients
                ongoing.clients.pop(response_id, None)
                ongoing.client_last_write.pop(response_id, None)
                client_count = len(ongoing.clients)
                if was_present:
                    logger.info(f"Handler cleanup: removed client from {key}, {client_count} remaining")
            
            try:
                await response.write_eof()
            except:
                pass
        
        return response
    
    async def handle_status(self, request: web.Request) -> web.Response:
        """Handle /ace/status endpoint"""
        stream_id = request.query.get('id', '')
        infohash = request.query.get('infohash', '')
        
        async with self.streams_lock:
            # Global status
            if not stream_id and not infohash:
                status = {
                    'streams': len(self.streams)
                }
                return web.json_response(status)
            
            # Specific stream status
            key = stream_id or infohash
            if key in self.streams:
                ongoing = self.streams[key]
                async with ongoing.lock:
                    status = {
                        'clients': len(ongoing.clients),
                        'stream_id': key,
                        'stat_url': ongoing.acestream.stat_url
                    }
                return web.json_response(status)
            else:
                return web.Response(status=404, text="Stream not found")
    
    async def start(self):
        """Start the aiohttp streaming server"""
        self.session = ClientSession()
        
        self.app = web.Application()
        self.app.router.add_get('/ace/getstream', self.handle_getstream)
        self.app.router.add_get('/ace/getstream/', self.handle_getstream)
        self.app.router.add_get('/ace/status', self.handle_status)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.listen_host, self.listen_port)
        await self.site.start()
        
        logger.info(f"Aiohttp streaming server started on {self.listen_host}:{self.listen_port}")
        logger.info(f"Connecting to AceStream at {self.scheme}://{self.acestream_host}:{self.acestream_port}")
        logger.info(f"Using NATIVE PYACEXY pattern (direct write, no queues)")
    
    async def stop(self):
        """Stop the aiohttp streaming server"""
        logger.info("Stopping aiohttp streaming server...")
        
        # Close all streams
        async with self.streams_lock:
            for stream in list(self.streams.values()):
                stream.done.set()
                if stream.fetch_task and not stream.fetch_task.done():
                    stream.fetch_task.cancel()
        
        if self.session:
            await self.session.close()
        
        if self.runner:
            await self.runner.cleanup()
        
        logger.info("Aiohttp streaming server stopped")
