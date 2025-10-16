"""
AceProxy API endpoints - Proxy to native aiohttp streaming server
"""
import logging
from typing import Optional, List, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import aiohttp

from app.utils.auth import get_db
from app.models import Channel
from app.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter()


def deduplicate_clients(clients_info: List[dict], time_threshold: int = 10) -> List[dict]:
    """
    Deduplicates client connections based on username+ip within time threshold.
    
    This handles IPTV clients that open multiple connections (e.g., IPTV Smarters
    opens one connection for the app and another for the video player).
    
    Args:
        clients_info: List of client dictionaries from streaming server
        time_threshold: Seconds within which connections are considered duplicates
    
    Returns:
        Deduplicated list with merged duplicate connections
    """
    if not clients_info:
        return []
    
    # Group by (username, ip)
    groups: Dict[str, List[dict]] = {}
    for client in clients_info:
        key = f"{client['username']}_{client['ip']}"
        if key not in groups:
            groups[key] = []
        groups[key].append(client)
    
    # Process each group
    result = []
    for group_key, connections in groups.items():
        if len(connections) == 1:
            # Single connection, no deduplication needed
            result.append(connections[0])
            continue
        
        # Sort by connection time
        connections.sort(key=lambda x: x['connected_at'])
        
        # Check if connections are within threshold
        first_time = datetime.fromisoformat(connections[0]['connected_at'])
        last_time = datetime.fromisoformat(connections[-1]['connected_at'])
        time_diff = (last_time - first_time).total_seconds()
        
        if time_diff <= time_threshold:
            # Merge as single logical user (connections within threshold)
            merged = {
                'username': connections[0]['username'],
                'ip': connections[0]['ip'],
                'user_agent': connections[0]['user_agent'],  # Use first UA
                'connected_at': connections[0]['connected_at'],
                'connection_count': len(connections),  # NEW FIELD - number of physical connections
                'physical_connections': [c['user_agent'] for c in connections]  # For tooltip
            }
            result.append(merged)
        else:
            # Different sessions (reconnections), keep separate
            result.extend(connections)
    
    return result


# Endpoints compatible with pyacexy - now proxying to aiohttp server
@router.get("/ace/getstream")
@router.get("/ace/getstream/")
async def ace_getstream(
    request: Request,
    id: Optional[str] = None,
    infohash: Optional[str] = None
):
    """
    Main AceStream proxy endpoint (pyacexy compatible)
    Stream AceStream content via HTTP - PROXIES to native aiohttp server
    Query params:
    - id: AceStream content ID
    - infohash: Torrent infohash
    """
    # Validate parameters
    if not id and not infohash:
        raise HTTPException(status_code=400, detail="Missing id or infohash parameter")
    
    if id and infohash:
        raise HTTPException(status_code=400, detail="Only one of id or infohash can be specified")
    
    # Get streaming server config
    config = get_config()
    
    # Build URL to aiohttp streaming server (internal)
    stream_id = id or infohash
    aiohttp_url = f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/getstream?{'id' if id else 'infohash'}={stream_id}"
    
    # Add any extra query parameters
    for key, value in request.query_params.items():
        if key not in ('id', 'infohash'):
            aiohttp_url += f"&{key}={value}"
    
    logger.info(f"Proxying stream {stream_id} to aiohttp server")
    
    # Proxy to aiohttp server
    async def stream_proxy():
        """Proxy stream from aiohttp server"""
        timeout = aiohttp.ClientTimeout(sock_read=60)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(aiohttp_url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Aiohttp server error: {response.status} - {error_text}")
                        return
                    
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            yield chunk
        except Exception as e:
            logger.error(f"Error proxying stream: {e}")
    
    return StreamingResponse(
        stream_proxy(),
        media_type="video/MP2T",
        headers={
            "Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.get("/ace/status")
async def ace_status(
    request: Request,
    id: Optional[str] = None,
    infohash: Optional[str] = None
):
    """
    Get AceStream proxy status (pyacexy compatible)
    Queries the aiohttp streaming server
    Query params:
    - id: AceStream content ID (optional - returns specific stream stats)
    - infohash: Torrent infohash (optional)
    """
    # Get streaming server config
    config = get_config()
    
    # Build URL to aiohttp streaming server
    aiohttp_url = f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/status"
    
    if id:
        aiohttp_url += f"?id={id}"
    elif infohash:
        aiohttp_url += f"?infohash={infohash}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(aiohttp_url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail="Stream not found")
                else:
                    raise HTTPException(status_code=response.status, detail="Error querying status")
    except aiohttp.ClientError as e:
        logger.error(f"Error querying aiohttp server: {e}")
        raise HTTPException(status_code=503, detail="Streaming server not available")


# Additional management endpoints (use AceProxyService for stats/management)
@router.get("/api/aceproxy/streams")
async def get_all_streams(request: Request, db: Session = Depends(get_db)):
    """Get all active streams from aiohttp server with channel names and client details"""
    try:
        # Get the aiohttp streaming server from app state
        aiohttp_server = request.app.state.aiohttp_streaming_server
        
        if not aiohttp_server:
            return {
                "status": "success",
                "total_streams": 0,
                "streams": []
            }
        
        # Get snapshot to avoid holding lock too long
        streams_list = []
        async with aiohttp_server.streams_lock:
            stream_items = list(aiohttp_server.streams.items())
        
        # Now process streams without holding the global lock
        for stream_id, ongoing_stream in stream_items:
            # Look up channel name in database
            channel = db.query(Channel).filter(Channel.acestream_id == stream_id).first()
            channel_name = channel.name if channel else stream_id[:20] + "..."
            
            # Get RAW client info from streaming server
            async with ongoing_stream.lock:
                raw_clients = []
                for client_info in ongoing_stream.clients.values():
                    raw_clients.append({
                        "username": client_info.username,
                        "ip": client_info.ip,
                        "user_agent": client_info.user_agent,
                        "connected_at": client_info.connected_at.isoformat()
                    })
            
            # DEDUPLICATION: Merge duplicate connections from same user
            # (e.g., IPTV Smarters opens 2 connections: app + video player)
            deduped_clients = deduplicate_clients(raw_clients)
            
            streams_list.append({
                "stream_id": stream_id,
                "channel_name": channel_name,
                "clients": deduped_clients,
                "client_count": len(deduped_clients),  # Deduplicated count
                "physical_connections": len(raw_clients),  # Total physical connections (for debugging)
                "created_at": ongoing_stream.created_at.isoformat() if hasattr(ongoing_stream, 'created_at') else None,
                "is_active": ongoing_stream.fetch_task and not ongoing_stream.fetch_task.done()
            })
        
        return {
            "status": "success",
            "total_streams": len(streams_list),
            "streams": streams_list
        }
    except Exception as e:
        logger.error(f"Error getting streams: {e}")
        raise HTTPException(status_code=503, detail="Streaming server not available")


@router.get("/api/aceproxy/streams/{stream_id}")
async def get_stream_info(stream_id: str, request: Request):
    """Get information about a specific stream"""
    config = get_config()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/status?id={stream_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "stream": data
                    }
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")
                else:
                    raise HTTPException(status_code=503, detail="Streaming server error")
    except aiohttp.ClientError as e:
        logger.error(f"Error querying aiohttp server: {e}")
        raise HTTPException(status_code=503, detail="Streaming server not available")


@router.delete("/api/aceproxy/streams/{stream_id}")
async def close_stream(stream_id: str, request: Request):
    """Force close a stream - not directly supported in aiohttp pattern"""
    # In pyacexy pattern, streams close automatically when no clients
    return {
        "status": "info",
        "message": "Streams close automatically when all clients disconnect (pyacexy pattern)"
    }


@router.get("/api/aceproxy/stats")
async def get_aceproxy_stats(request: Request):
    """Get overall AceProxy statistics"""
    config = get_config()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{config.acestream_streaming_host}:{config.acestream_streaming_port}/ace/status") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "stats": {
                            "total_streams": data.get("streams", 0),
                            "total_clients": 0,  # Not tracked in pyacexy pattern
                            "server_type": "aiohttp native pyacexy",
                            "streaming_port": config.acestream_streaming_port
                        }
                    }
                else:
                    raise HTTPException(status_code=503, detail="Streaming server not available")
    except aiohttp.ClientError as e:
        logger.error(f"Error querying aiohttp server: {e}")
        raise HTTPException(status_code=503, detail="Streaming server not available")
