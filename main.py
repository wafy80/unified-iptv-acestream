"""
Main application entry point for Unified IPTV AceStream Platform
"""
import asyncio
import logging
import sys
import os
import time
import hashlib
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from sqlalchemy.orm import Session

from setup import main as setup_app
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
from acestream_search import main as engine, get_options, __version__

# Get base directory
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(exist_ok=True)
(STATIC_DIR / "favicon").mkdir(exist_ok=True)

# Ensure logs directory exists
(BASE_DIR / "logs").mkdir(exist_ok=True)

# Configure logging with force=True to override any existing config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(BASE_DIR / 'logs/app.log'), mode='a')
    ],
    force=True
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
    favicon_path = STATIC_DIR / "favicon" / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    # Return 204 No Content if favicon doesn't exist
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

# Use two routing rules of Your choice where playlist extension does matter.
@app.get('/m3u')
@app.get('/search.m3u')
@app.get('/search.m3u8')
def search(request: Request):
    args = get_args(request)
    # return str(args)
    if args.xml_epg:
        content_type = 'text/xml'
    elif args.json:
        content_type = 'application/json'
    else:
        content_type = 'application/x-mpegURL'

    CACHE_DIR = 'tmp/cache'
    CACHE_EXPIRY = 300
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    def generate():               
        cache_key = hashlib.md5(str(args).encode('utf-8')).hexdigest()
        cache_file = os.path.join(CACHE_DIR, cache_key)
        temp_cache_file = cache_file + '.tmp'
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < CACHE_EXPIRY:
            with open(cache_file, 'r', encoding='utf-8') as f:
                for line in f:
                    yield line
        else:
            try:
                with open(temp_cache_file, 'w', encoding='utf-8') as f:                              
                    for page in engine(args):
                        f.write(page + '\n')
                os.rename(temp_cache_file, cache_file)
            finally: 
                with open(cache_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        yield line

    if 'version' in args:
        return Response(__version__ + '\n', media_type='text/plain')
    if 'help' in args:
        return Response(args.help, media_type='text/plain')
    if 'usage' in args:
        return Response(args.usage, media_type='text/plain')
    if args.url:
        redirect_url = next(x for x in generate()).strip('\n')
        response = Response('', media_type='')
        response.headers['Location'] = redirect_url
        response.headers['Content-Type'] = ''
        response.status_code = 302
        return response
    return Response(''.join(generate()), media_type=content_type)

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

def get_args(request: Request):
    opts = {'prog': str(request.base_url)}
    for item in request.query_params:
        opts[item] = request.query_params[item]
    if 'query' not in opts:
        opts['query'] = ''
    args = get_options(opts)
    return args

if __name__ == "__main__":
    import uvicorn
    
    setup_app()  # Run setup on startup
    config = get_config()
    
    # Configure uvicorn logging to also write to file
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": str(BASE_DIR / "logs/app.log"),
        "formatter": "default",
        "mode": "a"
    }
    log_config["loggers"]["uvicorn"]["handlers"].append("file")
    log_config["loggers"]["uvicorn.access"]["handlers"].append("file")
    
    # Run unified server on single port
    uvicorn.run(
        "main:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.server_debug,
        log_level="info",
        log_config=log_config
    )
