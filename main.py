"""
Main application entry point for Unified IPTV AceStream Platform
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import get_config
from app.utils.auth import create_user
from app.services.aceproxy_service import AceProxyService
from app.services.aiohttp_streaming_server import AiohttpStreamingServer
from app.services.scraper_service import ImprovedScraperService
from app.services.epg_service import EPGService
from app.api import xtream
from app.api import dashboard
from app.api import api_endpoints
from app.api import aceproxy
from app.api import logs
from app.models import User, ScraperURL, EPGSource, Setting

# Get base directory
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(exist_ok=True)
(STATIC_DIR / "favicon").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(BASE_DIR / 'logs/app.log'))
    ]
)

logger = logging.getLogger(__name__)


# Global services
aceproxy_service: AceProxyService = None
aiohttp_streaming_server: AiohttpStreamingServer = None
scraper_service: ImprovedScraperService = None  # Using improved scraper
epg_service: EPGService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global aceproxy_service, aiohttp_streaming_server, scraper_service, epg_service
    
    logger.info("Starting Unified IPTV AceStream Platform...")
    
    # Initialize configuration first
    config = get_config()
    
    # Initialize database with config
    from app.utils.auth import init_db as initialize_database
    initialize_database()
    
    # Now we can import SessionLocal
    from app.utils.auth import SessionLocal
    
    # Create database session for initialization
    db = SessionLocal()
    
    try:
        # Check/create admin user
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            logger.info("Creating admin user...")
            create_user(
                db,
                username=config.admin_username,
                password=config.admin_password,
                is_admin=True
            )
            logger.info(f"Admin user created: {config.admin_username}")
        
        # Initialize scraper URLs if configured
        scraper_urls_list = config.get_scraper_urls_list()
        if scraper_urls_list:
            for url in scraper_urls_list:
                existing = db.query(ScraperURL).filter(ScraperURL.url == url).first()
                if not existing:
                    scraper_url = ScraperURL(url=url, is_enabled=True)
                    db.add(scraper_url)
            db.commit()
        
        # Initialize EPG sources if configured
        epg_sources_list = config.get_epg_sources_list()
        if epg_sources_list:
            for url in epg_sources_list:
                existing = db.query(EPGSource).filter(EPGSource.url == url).first()
                if not existing:
                    epg_source = EPGSource(url=url, is_enabled=True)
                    db.add(epg_source)
            db.commit()
        
        # Initialize services
        if config.acestream_enabled:
            logger.info("Starting aiohttp streaming server (native pyacexy pattern)...")
            aiohttp_streaming_server = AiohttpStreamingServer(
                acestream_host=config.acestream_engine_host,
                acestream_port=config.acestream_engine_port,
                listen_host=config.acestream_streaming_host,
                listen_port=config.acestream_streaming_port,
                chunk_size=config.acestream_chunk_size,
                empty_timeout=config.acestream_empty_timeout,
                no_response_timeout=config.acestream_no_response_timeout,
            )
            await aiohttp_streaming_server.start()
            
            # Keep old AceProxyService for compatibility (stats, management API)
            logger.info("Starting AceProxy service (for API/stats)...")
            aceproxy_service = AceProxyService(
                acestream_host=config.acestream_engine_host,
                acestream_port=config.acestream_engine_port,
                timeout=config.acestream_timeout
            )
            await aceproxy_service.start()
            
            # Store in app state
            app.state.aceproxy_service = aceproxy_service
            app.state.aiohttp_streaming_server = aiohttp_streaming_server
        else:
            app.state.aceproxy_service = None
            app.state.aiohttp_streaming_server = None
        
        logger.info("Starting Scraper service...")
        scraper_service = ImprovedScraperService(
            update_interval=config.scraper_update_interval
        )
        await scraper_service.start()
        
        logger.info("Starting EPG service...")
        epg_service = EPGService(db)
        await epg_service.start()
        
        # Start background tasks
        asyncio.create_task(scraper_service.auto_scrape_loop())
        asyncio.create_task(epg_service.auto_update_loop())
        
        logger.info("All services started successfully")
        
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    
    if aiohttp_streaming_server:
        await aiohttp_streaming_server.stop()
    
    if aceproxy_service:
        await aceproxy_service.stop()
    
    if scraper_service:
        await scraper_service.stop()
    
    if epg_service:
        await epg_service.stop()
    
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Unified IPTV AceStream Platform",
    description="Complete IPTV platform with AceStream support, Xtream Codes API, EPG, and more",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Favicon endpoint
@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to avoid 404 errors"""
    from fastapi.responses import FileResponse
    favicon_path = STATIC_DIR / "favicon" / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    # Return 204 No Content if favicon doesn't exist
    from fastapi.responses import Response
    return Response(status_code=204)

# Include routers - ORDER MATTERS! Most specific first
# AceProxy routes without prefix for pyacexy compatibility  
app.include_router(aceproxy.router, tags=["AceProxy"])
app.include_router(logs.router, prefix="/api", tags=["Logs"])
app.include_router(api_endpoints.router, prefix="/api", tags=["API"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(xtream.router, tags=["Xtream API"])  # Last because it catches all paths

# Health check endpoint
@app.get("/health")
@app.get("/api/health")
async def health_check(request: Request):
    """Health check endpoint"""
    config = get_config()
    
    health_status = {
        "status": "healthy",
        "services": {
            "aceproxy": aceproxy_service is not None if config.acestream_enabled else "disabled",
            "scraper": scraper_service is not None,
            "epg": epg_service is not None
        }
    }
    
    # Get service statistics from aiohttp streaming server
    active_streams_count = 0
    if config.acestream_enabled and aiohttp_streaming_server:
        try:
            # Quick lock to get count only
            async with aiohttp_streaming_server.streams_lock:
                active_streams_count = len(aiohttp_streaming_server.streams)
        except Exception as e:
            logger.error(f"Error getting stream count: {e}")
    
    health_status["aceproxy_streams"] = active_streams_count
    
    return health_status


@app.get("/")
async def root():
    """Root endpoint"""
    config = get_config()
    
    return {
        "name": "Unified IPTV AceStream Platform",
        "version": "1.0.0",
        "endpoints": {
            "xtream_api": f"http://{config.server_host}:{config.server_port}/player_api.php",
            "m3u_playlist": f"http://{config.server_host}:{config.server_port}/get.php",
            "epg": f"http://{config.server_host}:{config.server_port}/xmltv.php",
            "aceproxy": f"http://{config.server_host}:{config.server_port}/ace/getstream",
            "health": "/health",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    
    # Run unified server on single port
    uvicorn.run(
        "main:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.server_debug,
        log_level="info"
    )
