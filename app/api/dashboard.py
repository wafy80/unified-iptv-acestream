"""
Web UI Routes for Dashboard
"""
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import secrets

from app.utils.auth import get_db
from app.models import User, Channel, Category
from app.config import get_config

# Get absolute path to templates directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
security = HTTPBasic()


async def verify_admin_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify admin credentials for dashboard access"""
    config = get_config()
    
    # Check username
    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        config.admin_username.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        config.admin_password.encode("utf8")
    )
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    username: str = Depends(verify_admin_credentials)
):
    """Dashboard page - requires authentication"""
    config = get_config()
    
    # Get stats
    user_count = db.query(User).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_count": user_count,
        "server_url": f"http://{config.server_host}:{config.server_port}",
        "timezone": config.server_timezone,
        "acestream_host": config.acestream_engine_host,
        "acestream_port": config.acestream_engine_port,
        "username": username,
    })


@router.get("/channels", response_class=HTMLResponse)
async def channels(
    request: Request,
    username: str = Depends(verify_admin_credentials)
):
    """Channels page - requires authentication"""
    return templates.TemplateResponse("channels.html", {
        "request": request,
        "username": username
    })


@router.get("/users", response_class=HTMLResponse)
async def users(
    request: Request,
    username: str = Depends(verify_admin_credentials)
):
    """Users page - requires authentication"""
    return templates.TemplateResponse("users.html", {
        "request": request,
        "username": username
    })


@router.get("/scraper", response_class=HTMLResponse)
async def scraper(
    request: Request,
    username: str = Depends(verify_admin_credentials)
):
    """Scraper page - requires authentication"""
    return templates.TemplateResponse("scraper.html", {
        "request": request,
        "username": username
    })


@router.get("/epg", response_class=HTMLResponse)
async def epg(
    request: Request,
    username: str = Depends(verify_admin_credentials)
):
    """EPG page - requires authentication"""
    return templates.TemplateResponse("epg.html", {
        "request": request,
        "username": username
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings(
    request: Request,
    username: str = Depends(verify_admin_credentials)
):
    """Settings page - requires authentication"""
    config = get_config()
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config,
        "username": username
    })
