"""
API endpoints for dashboard data
"""
import logging
import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.utils.auth import get_db
from app.models import Channel, User, Category, ScraperURL, EPGSource

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request, db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # Get channel stats
    total_channels = db.query(Channel).count()
    online_channels = db.query(Channel).filter(Channel.is_online == True).count()
    active_channels = db.query(Channel).filter(Channel.is_active == True).count()
    
    # Get user stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Get category stats
    total_categories = db.query(Category).count()
    
    # Get scraper stats
    total_scraper_urls = db.query(ScraperURL).count()
    enabled_scraper_urls = db.query(ScraperURL).filter(ScraperURL.is_enabled == True).count()
    
    # Get EPG stats
    total_epg_sources = db.query(EPGSource).count()
    
    # Get active streams from aiohttp server
    active_streams = 0
    total_clients = 0
    try:
        aiohttp_server = request.app.state.aiohttp_streaming_server
        if aiohttp_server:
            # Get snapshot to avoid holding lock too long
            async with aiohttp_server.streams_lock:
                streams_snapshot = list(aiohttp_server.streams.values())
            
            active_streams = len(streams_snapshot)
            for stream in streams_snapshot:
                async with stream.lock:
                    total_clients += len(stream.clients)
    except Exception as e:
        logger.error(f"Error getting active streams: {e}")
    
    # Check AceStream engine health
    acestream_engine_status = {
        "status": "disabled",
        "available": False
    }
    try:
        aceproxy = request.app.state.aceproxy_service
        if aceproxy:
            acestream_engine_status = await aceproxy.check_engine_health()
    except Exception as e:
        logger.error(f"Error checking AceStream engine health: {e}")
        acestream_engine_status = {
            "status": "error",
            "available": False,
            "message": str(e)
        }
    
    return {
        "total_channels": total_channels,
        "online_channels": online_channels,
        "active_channels": active_channels,
        "total_users": total_users,
        "active_users": active_users,
        "total_categories": total_categories,
        "scraper_urls": total_scraper_urls,
        "enabled_scraper_urls": enabled_scraper_urls,
        "epg_sources": total_epg_sources,
        "active_streams": active_streams,
        "active_connections": total_clients,
        "acestream_engine": acestream_engine_status
    }


@router.get("/channels")
async def get_channels(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get channels list"""
    
    channels = db.query(Channel).filter(
        Channel.is_active == True
    ).order_by(
        Channel.display_order, Channel.name
    ).limit(limit).offset(offset).all()
    
    return [
        {
            "id": channel.id,
            "name": channel.name,
            "acestream_id": channel.acestream_id,
            "category": channel.category.name if channel.category else None,
            "logo_url": channel.logo_url,
            "is_online": channel.is_online,
            "is_active": channel.is_active,
            "created_at": channel.created_at.isoformat()
        }
        for channel in channels
    ]


@router.post("/scraper/trigger")
async def trigger_scraping(db: Session = Depends(get_db)):
    """Trigger manual scraping"""
    from main import scraper_service
    
    logger.info("=== MANUAL SCRAPING TRIGGERED VIA API ===")
    
    if not scraper_service:
        logger.error("Scraper service not initialized")
        return {"status": "error", "message": "Scraper service not initialized"}
    
    try:
        # Pass db session to scraper
        start_time = time.time()
        logger.info("Starting scraping process...")
        results = await scraper_service.scrape_m3u_sources(db)
        elapsed = time.time() - start_time
        
        total_channels = sum(results.values())
        
        logger.info(f"=== SCRAPING COMPLETED: {total_channels} channels from {len(results)} source(s) in {elapsed:.2f}s ===")
        
        return {
            "status": "success",
            "message": f"Scraped {total_channels} channels from {len(results)} source(s)",
            "details": {
                "total_channels": total_channels,
                "sources_processed": len(results),
                "results": results,
                "elapsed_seconds": round(elapsed, 2)
            }
        }
    except Exception as e:
        logger.error(f"Error triggering scraping: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/epg/update")
async def update_epg(db: Session = Depends(get_db)):
    """Trigger EPG update"""
    # TODO: Implement EPG update trigger
    return {"status": "triggered", "message": "EPG update will start shortly"}


@router.post("/channels/check")
async def check_channels(db: Session = Depends(get_db)):
    """Check channel status"""
    # TODO: Implement channel status check
    return {"status": "triggered", "message": "Channel check will start shortly"}
