"""
Xtream Codes API Implementation
Compatible with IPTV Smarters, Perfect Player, TiviMate, etc.
"""
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.models import User, Channel, Category, EPGProgram
from app.services.epg_service import EPGService
from app.services.aceproxy_service import AceProxyService
from app.utils.auth import verify_user, get_db
from app.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamHelper:
    """
    Helper class for managing IPTV streams.
    """
    
    @staticmethod
    async def receive_stream(url, chunk_size=1024, timeout=None):
        """
        Receive a stream from a URL and return it in data chunks.
        
        Args:
            url (str): The stream URL to receive
            chunk_size (int): Size of data chunks in bytes (default: 1024)
            timeout (int): Socket read timeout in seconds (default: None = no timeout)
            
        Yields:
            bytes: Stream data chunks
            
        Raises:
            aiohttp.ClientError: If an HTTP request error occurs
            asyncio.TimeoutError: If socket read exceeds timeout
        """
        # Use sock_read timeout for streaming (not total timeout)
        # This allows infinite streaming but with timeout on chunk reads
        if timeout:
            timeout_config = aiohttp.ClientTimeout(sock_read=timeout)
        else:
            timeout_config = aiohttp.ClientTimeout(sock_read=60)  # 60s per chunk
        
        try:
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(url) as response:
                    # Verify the response is valid
                    if response.status != 200:
                        logger.error(f"HTTP request error: {response.status} - {response.reason}")
                        raise aiohttp.ClientError(f"HTTP {response.status}: {response.reason}")
                    
                    logger.info(f"Streaming from {url} started successfully")
                    
                    async for data_bytes in response.content.iter_chunked(chunk_size):
                        yield data_bytes
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout during connection to {url}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Client error during connection to {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection to {url}: {str(e)}")
            raise
        finally:
            logger.info(f"Streaming from {url} terminated")


class ClientTracker:
    """
    Track client connections to streams.
    """
    def __init__(self):
        self.clients = {}
    
    def add_client(self, ip, port, channel_watch):
        import time
        self.clients[f"{ip}:{port}"] = {
            "url": channel_watch,
            "time_create": int(time.time()),
        }
    
    def get_client(self, ip, port, requested_url=None):
        import time
        # Check if client is in the list
        logger.debug(f"Current clients: {self.clients}")
        client_key = f"{ip}:{port}"
        if client_key not in self.clients:
            return False
        
        # If a specific URL is requested, check if it matches
        # If not, return False to force creation of new stream
        if requested_url and self.clients[client_key]["url"] != requested_url:
            logger.debug(f"Client {client_key} requesting different URL, forcing new stream")
            return False
        
        # Update time_create
        self.clients[client_key]["time_create"] = int(time.time())
        return self.clients[client_key]["url"]
    
    def remove_client(self):
        import time
        current_time = int(time.time())
        for client in list(self.clients):
            if current_time - self.clients[client]["time_create"] > 15:
                del self.clients[client]


# Global client tracker
CLIENT = ClientTracker()


def get_base_url(request: Request) -> str:
    """Get base URL from request"""
    config = get_config()
    
    # Check for reverse proxy headers
    forwarded_proto = request.headers.get("x-forwarded-proto", "http")
    forwarded_host = request.headers.get("x-forwarded-host")
    
    if forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"
    
    return f"http://{config.server_host}:{config.server_port}"


@router.get("/player_api.php")
async def player_api(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    action: Optional[str] = None,
    category_id: Optional[str] = None,
    stream_id: Optional[int] = None,
    vod_id: Optional[int] = None,
    series_id: Optional[int] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Main Xtream Codes API endpoint"""
    
    # Verify user authentication
    if not username or not password:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # Check expiry
    if user.expiry_date and user.expiry_date < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Account expired")
    
    base_url = get_base_url(request)
    config = get_config()
    
    # Handle different actions
    if not action:
        # Return user info and server info (Xtream Codes format - EXACT compatibility)
        now = datetime.utcnow()
        response = {
            "user_info": {
                "username": user.username,
                "password": password,
                "message": config.message_of_day if hasattr(config, 'message_of_day') else "",
                "auth": 1,
                "status": "Active" if user.is_active else "Inactive",
                "is_trial": 0 if not user.is_trial else 1,
                "active_cons": 0,
                "created_at": int(user.created_at.timestamp()),
                "max_connections": int(user.max_connections),
                "allowed_output_formats": ["m3u8", "ts"]
            },
            "server_info": {
                "url": config.server_host,
                "port": str(config.server_port),
                "https_port": str(config.server_port),
                "server_protocol": "http",
                "rtmp_port": "0",
                "timezone": "GMT",
                "timestamp_now": int(now.timestamp()),
                "time_now": now.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        # Add exp_date only if set (like reference)
        if user.expiry_date:
            response["user_info"]["exp_date"] = int(user.expiry_date.timestamp())
        
        return response
    
    elif action == "get_live_categories":
        # Return live stream categories (Xtream format)
        categories = db.query(Category).order_by(Category.display_order, Category.name).all()
        
        return [
            {
                "category_id": str(cat.id),
                "category_name": cat.name,
                "parent_id": cat.parent_id if cat.parent_id else 0
            }
            for cat in categories
        ]
    
    elif action == "get_live_streams":
        # Return live streams (Xtream Codes format - EXACT field order)
        query = db.query(Channel).filter(Channel.is_active == True)
        
        if category_id:
            query = query.filter(Channel.category_id == int(category_id))
        
        channels = query.order_by(Channel.display_order, Channel.name).all()
        
        result = []
        num = 0
        for channel in channels:
            num += 1
            
            # Build category_ids array (integers not strings)
            category_ids = [int(channel.category_id)] if channel.category_id else []
            
            # EXACT field order as reference
            result.append({
                "num": num,
                "name": channel.name,
                "stream_type": "live",
                "stream_id": channel.id,
                "stream_icon": channel.logo_url or "",
                "epg_channel_id": channel.epg_id or "",
                "added": str(int(channel.created_at.timestamp())),
                "is_adult": "0",
                "category_id": str(channel.category_id) if channel.category_id else "0",
                "category_ids": category_ids,
                "custom_sid": None,
                "tv_archive": 0,
                "direct_source": "",
                "tv_archive_duration": 0
            })
        
        return result
    
    elif action == "get_vod_categories":
        # VOD not implemented yet
        return []
    
    elif action == "get_vod_streams":
        # VOD not implemented yet
        return []
    
    elif action == "get_series_categories":
        # Series not implemented yet
        return []
    
    elif action == "get_series":
        # Series not implemented yet
        return []
    
    elif action == "get_series_info":
        # Series not implemented yet
        return {}
    
    elif action == "get_vod_info":
        # VOD info not implemented yet
        return {}
    
    elif action == "get_short_epg" and stream_id:
        # Return short EPG for stream using new method
        epg_service = EPGService(db)
        
        channel = db.query(Channel).filter(Channel.id == stream_id).first()
        if not channel:
            return {"epg_listings": []}
        
        # Use the new get_short_epg method
        return epg_service.get_short_epg(channel.id, limit=limit or 4)
    
    elif action == "get_simple_data_table" and stream_id:
        # Return simple EPG data using new method
        epg_service = EPGService(db)
        
        channel = db.query(Channel).filter(Channel.id == stream_id).first()
        if not channel:
            return {"epg_listings": []}
        
        # Use the new get_simple_data_table method
        return epg_service.get_simple_data_table(channel.id)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


@router.get("/panel_api.php")
async def panel_api(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Panel API endpoint (Xtream Codes compatible)"""
    
    # Verify user authentication
    if not username or not password:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    # Check expiry
    if user.expiry_date and user.expiry_date < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Account expired")
    
    config = get_config()
    
    # Return panel info (same format as player_api without action)
    return {
        "user_info": {
            "username": user.username,
            "password": password,
            "message": config.message_of_day if hasattr(config, 'message_of_day') else "",
            "auth": 1,
            "status": "Active" if user.is_active else "Disabled",
            "exp_date": int(user.expiry_date.timestamp()) if user.expiry_date else None,
            "is_trial": int(user.is_trial),
            "active_cons": 0,
            "created_at": int(user.created_at.timestamp()),
            "max_connections": int(user.max_connections),
            "allowed_output_formats": ["m3u8", "ts", "rtmp"]
        },
        "server_info": {
            "xui": True,
            "version": "1.0.0",
            "url": config.server_host,
            "port": str(config.server_port),
            "https_port": "443",
            "server_protocol": "http",
            "rtmp_port": "1935",
            "timestamp_now": int(datetime.utcnow().timestamp()),
            "time_now": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": config.server_timezone
        }
    }


@router.get("/live/{username}/{password}/{stream_id}")
@router.get("/live/{username}/{password}/{stream_id}.{extension}")
async def stream_live_channel(
    request: Request,
    username: str,
    password: str,
    stream_id: int,
    extension: Optional[str] = "ts",
    db: Session = Depends(get_db)
):
    """Stream a live channel (Xtream format)"""
    
    # Verify user
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get channel
    channel = db.query(Channel).filter(Channel.id == stream_id, Channel.is_active == True).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    config = get_config()
    
    # Determine stream URL
    stream_url = None
    
    # Check if channel has AceStream ID
    if channel.acestream_id:
        # Build the expected stream URL for this channel
        real_client_ip = request.client.host
        real_user_agent = request.headers.get("User-Agent", "Unknown")
        
        # URL encode parameters to handle special characters
        from urllib.parse import quote
        expected_stream_url = (
            f"http://127.0.0.1:{config.server_port}/ace/getstream"
            f"?id={channel.acestream_id}"
            f"&username={username}"
            f"&client_ip={quote(real_client_ip)}"
            f"&client_ua={quote(real_user_agent)}"
        )
        
        # Add query parameters if present
        if request.query_params:
            for key, value in request.query_params.items():
                expected_stream_url += f"&{key}={value}"
        
        # Check if we already have a client session for THIS specific stream
        stream_url = CLIENT.get_client(request.client.host, str(request.client.port), expected_stream_url)
        
        if stream_url is False:
            # Use the expected stream URL (new stream needed)
            stream_url = expected_stream_url
        else:
            CLIENT.remove_client()
    
    # Check if channel has direct URL (from M3U)
    elif channel.stream_url:
        stream_url = channel.stream_url
    
    if not stream_url:
        raise HTTPException(status_code=404, detail="No stream URL available")
    
    # Track client
    CLIENT.add_client(request.client.host, str(request.client.port), stream_url)
    
    logger.info(f"Streaming {stream_id} from: {stream_url}")
    
    # Stream the content (both AceStream and direct streams go through StreamHelper)
    return StreamingResponse(
        StreamHelper.receive_stream(stream_url),
        media_type="video/mp2t"
    )


@router.get("/live/{username}/{password}/{file_path:path}")
async def stream_live_container(
    username: str, 
    password: str, 
    file_path: str, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle incomplete links to lists with video containers (compatibility endpoint)"""
    
    logger.info(f"Container request for path: {file_path}")
    
    # Verify user
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get the stream URL from client tracker
    stream_url = CLIENT.get_client(request.client.host, str(request.client.port))
    
    if not stream_url:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Replace the last segment with the file path
    stream_url = stream_url.replace(stream_url.split("/")[-1], "")
    stream_url = stream_url + file_path
    
    return StreamingResponse(
        StreamHelper.receive_stream(stream_url),
        media_type="video/mp2t"
    )


@router.get("/movie/{username}/{password}/{vod_id}.{ext}")
async def stream_movie(
    username: str, 
    password: str, 
    vod_id: str, 
    ext: str, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Stream a movie/VOD (Xtream format)"""
    
    # Verify user
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # TODO: Implement VOD streaming when VOD support is added
    # For now, return 404
    raise HTTPException(status_code=404, detail="VOD not implemented yet")


@router.get("/series/{username}/{password}/{episode_id}.{ext}")
async def stream_series(
    username: str, 
    password: str, 
    episode_id: str, 
    ext: str, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Stream a series episode (Xtream format)"""
    
    # Verify user
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # TODO: Implement series streaming when series support is added
    # For now, return 404
    raise HTTPException(status_code=404, detail="Series not implemented yet")


@router.get("/{username}/{password}/{stream_id}")
@router.get("/{username}/{password}/{stream_id}.{extension}")
async def stream_channel(
    request: Request,
    username: str,
    password: str,
    stream_id: int,
    extension: Optional[str] = "ts",
    db: Session = Depends(get_db)
):
    """Stream a channel (Xtream format) - Fallback route"""
    
    # Redirect to /live/ endpoint
    return await stream_live_channel(request, username, password, stream_id, extension, db)


@router.get("/get.php")
async def get_m3u_playlist(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    type: str = "m3u_plus",
    output: str = "ts",
    db: Session = Depends(get_db)
):
    """Get M3U playlist (Xtream format)"""
    
    if not username or not password:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    base_url = get_base_url(request)
    
    # Generate M3U
    m3u_lines = [f'#EXTM3U url-tvg="{base_url}/xmltv.php?username={username}&password={password}"']
    
    channels = db.query(Channel).filter(Channel.is_active == True).order_by(Channel.display_order, Channel.name).all()
    
    for channel in channels:
        """
        if not channel.acestream_id:
            continue
        """

        # Build EXTINF line
        extinf_parts = [f'#EXTINF:-1']
        
        if channel.logo_url:
            extinf_parts.append(f'tvg-logo="{channel.logo_url}"')
        
        if channel.epg_id:
            extinf_parts.append(f'tvg-id="{channel.epg_id}"')
        
        if channel.category:
            extinf_parts.append(f'group-title="{channel.category.name}"')
        
        extinf_parts.append(f',{channel.name}')
        
        m3u_lines.append(' '.join(extinf_parts))
        
        # Build stream URL - use /live/ prefix for clarity
        stream_url = f"{base_url}/live/{username}/{password}/{channel.id}.{output}"
        m3u_lines.append(stream_url)
    
    m3u_content = '\n'.join(m3u_lines)
    
    return Response(content=m3u_content, media_type="audio/x-mpegurl")


@router.get("/xmltv.php")
async def get_epg_xml(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get EPG in XMLTV format (Xtream API compatible)
    Endpoint: /xmltv.php?username=X&password=Y
    """
    
    if username and password:
        user = verify_user(db, username, password)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    epg_service = EPGService(db)
    xml_content = epg_service.generate_epg_xml()
    
    return Response(content=xml_content, media_type="application/xml")


@router.post("/epg/update")
async def trigger_epg_update(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Manually trigger EPG update
    Requires admin credentials
    """
    
    if not username or not password:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    epg_service = EPGService(db)
    await epg_service.start()
    
    try:

        config = get_config()
        xmltv_sources = config.get_epg_sources_list()
        
        if xmltv_sources:
            logger.info("Triggering XMLTV EPG update...")
            programs_count = await epg_service.update_all_epg()
            return {
                "success": True,
                "method": "xmltv",
                "programmes_updated": programs_count,
                "message": f"EPG updated successfully using XMLTV method"
            }
        else:
            return {
                "success": False,
                "method": "xmltv",
                "error": "No XMLTV sources configured"
            }

    except Exception as e:
        logger.error(f"Error updating EPG: {e}")
        raise HTTPException(status_code=500, detail=f"EPG update failed: {str(e)}")
    finally:
        await epg_service.stop()


@router.get("/epg/status")
async def get_epg_status(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get EPG status and statistics
    Requires authentication
    """
    
    if not username or not password:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    config = get_config()
    
    # Get EPG statistics
    total_channels = db.query(Channel).count()
    channels_with_epg = db.query(Channel).filter(Channel.epg_id.isnot(None)).count()
    total_programs = db.query(EPGProgram).count()
    
    # Get programs count by time range
    now = datetime.utcnow()
    current_programs = db.query(EPGProgram).filter(
        EPGProgram.start_time <= now,
        EPGProgram.end_time > now
    ).count()
    
    future_programs = db.query(EPGProgram).filter(
        EPGProgram.start_time > now
    ).count()
    
    # Get XMLTV sources configuration
    xmltv_sources = config.get_epg_sources_list()
    
    # Get database sources
    from app.models import EPGSource
    db_sources = db.query(EPGSource).all()
    
    return {
        "total_channels": total_channels,
        "channels_with_epg_id": channels_with_epg,
        "total_programs": total_programs,
        "current_programs": current_programs,
        "future_programs": future_programs,
        "xmltv_sources": xmltv_sources,
        "xmltv_sources_count": len(xmltv_sources) if xmltv_sources else 0,
        "database_sources": [
            {
                "id": src.id,
                "url": src.url,
                "enabled": src.is_enabled,
                "last_updated": src.last_updated.isoformat() if src.last_updated else None,
                "programs_found": src.programs_found
            }
            for src in db_sources
        ],
        "database_sources_count": len(db_sources),
        "update_interval": config.epg_update_interval,
        "cache_file": config.epg_cache_file
    }


@router.get("/epg/channel/{channel_id}")
async def get_channel_epg(
    channel_id: int,
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    hours: int = Query(24, description="Hours of EPG to return"),
    db: Session = Depends(get_db)
):
    """
    Get EPG for a specific channel
    Returns programmes for the next N hours
    """
    
    if username and password:
        user = verify_user(db, username, password)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    epg_service = EPGService(db)
    programs = epg_service.get_programs(channel_id, hours=hours)
    
    return {
        "channel_id": channel.id,
        "channel_name": channel.name,
        "epg_id": channel.epg_id,
        "programs": [
            {
                "id": prog.id,
                "title": prog.title,
                "description": prog.description,
                "start_time": prog.start_time.isoformat(),
                "end_time": prog.end_time.isoformat(),
                "duration_minutes": int((prog.end_time - prog.start_time).total_seconds() / 60),
                "category": prog.category,
                "icon_url": prog.icon_url,
                "rating": prog.rating
            }
            for prog in programs
        ],
        "total_programs": len(programs)
    }


@router.post("/epg/clean_duplicates")
async def clean_epg_duplicates(
    request: Request,
    username: Optional[str] = None,
    password: Optional[str] = None,
    channel_id: Optional[int] = Query(None, description="Clean specific channel, or all if not specified"),
    db: Session = Depends(get_db)
):
    """
    Clean duplicate EPG programs from database
    Requires admin credentials
    """
    
    if not username or not password:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_user(db, username, password)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    epg_service = EPGService(db)
    
    try:
        removed_count = epg_service.clean_duplicate_programs(channel_id)
        
        return {
            "success": True,
            "duplicates_removed": removed_count,
            "message": f"Successfully removed {removed_count} duplicate programs"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clean duplicates: {str(e)}")

