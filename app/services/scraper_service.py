"""
M3U/EPG Scraper Service - Based on xtream_api working implementation
"""
import asyncio
import logging
import time
import re
import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models import Channel, Category, ScraperURL, EPGSource
from app.utils.auth import SessionLocal  # Fix import

logger = logging.getLogger(__name__)


class M3UParser:
    """Parser for M3U playlist files"""
    
    def __init__(self, m3u_url: str):
        self.m3u_url = m3u_url
        self.m3u_list = []
        
    def _get_m3u_list(self) -> List[str]:
        """Download M3U playlist and return as list of lines"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36"
        }
        timeout = 30
        
        try:
            logger.info(f"Downloading M3U from: {self.m3u_url}")
            request = requests.get(self.m3u_url, timeout=timeout, headers=headers)
            
            if request.status_code == 200:
                logger.info(f"M3U downloaded successfully, size: {len(request.text)} bytes")
                return request.text.splitlines()
            else:
                logger.error(f"Error downloading M3U: HTTP {request.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error("M3U download timeout")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"M3U download error: {e}")
            return []
    
    def _extract_acestream_id(self, url: str) -> Optional[str]:
        """Extract acestream ID from various URL formats"""
        if not url:
            return None
            
        # Pattern for acestream:// URLs
        acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        match = acestream_pattern.search(url)
        if match:
            return match.group(1)
        
        # Pattern for URLs containing acestream ID as parameter
        # e.g., http://example.com/stream?id=ACESTREAM_ID
        id_pattern = re.compile(r'[?&]id=([\w\d]+)')
        match = id_pattern.search(url)
        if match:
            return match.group(1)
        
        # Pattern for direct 40-char hex IDs in URL path
        # e.g., http://example.com/ACESTREAM_ID
        hex_pattern = re.compile(r'/([a-fA-F0-9]{40})(?:[/?]|$)')
        match = hex_pattern.search(url)
        if match:
            return match.group(1)
            
        return None
    
    async def parse_m3u(self, db: Session) -> int:
        """Parse M3U and save to database - Based on acestream-scraper logic"""
        self.m3u_list = self._get_m3u_list()
        
        if not self.m3u_list:
            logger.error("No M3U data to parse")
            return 0
        
        logger.info(f"Parsing {len(self.m3u_list)} lines from M3U")
        
        channels_added = 0
        categories_cache = {}
        flag = 0
        data = {}
        
        for line in self.m3u_list:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or (line.startswith("#") and not line.startswith("#EXTINF:")):
                continue
            
            # Parse channel info
            if line.startswith("#EXTINF:"):
                flag = 1
                data = {}
                
                # Extract stream icon
                icon_match = re.search(r'tvg-logo="(.+?)"', line)
                data["stream_icon"] = icon_match.group(1).strip() if icon_match else ""
                
                # Extract name
                name_match = re.search(r'tvg-name="(.+?)"', line)
                if name_match:
                    data["name"] = name_match.group(1).strip()
                else:
                    # Fallback to text after comma
                    comma_match = re.search(r',(.+)', line)
                    data["name"] = comma_match.group(1).strip() if comma_match else "Unknown"
                
                # Extract category
                group_match = re.search(r'group-title="(.+?)"', line)
                data["group_title"] = group_match.group(1).strip() if group_match else "Uncategorized"
                
                # Extract EPG ID
                epg_match = re.search(r'tvg-id="(.+?)"', line)
                data["epg_channel_id"] = epg_match.group(1).strip() if epg_match else ""
                
            # Parse stream URL - Extract acestream ID from various formats
            elif flag == 1 and line:
                flag = 0
                
                # Extract acestream ID from URL
                acestream_id = self._extract_acestream_id(line)
                if acestream_id:
                    data["acestream_id"] = acestream_id
                    data["stream_url"] = f"acestream://{acestream_id}"
                    logger.debug(f"Extracted acestream ID: {acestream_id} from: {line}")
                else:
                    if line.startswith("http"):
                        # Keep regular HTTP URLs as-is
                        data["stream_url"] = line
                    else:
                        # Skip invalid URLs
                        logger.warning(f"Skipping invalid URL: {line}")
                        continue
                
                # Save channel to database
                try:
                    # Get or create category
                    category_name = data.get("group_title", "Uncategorized")
                    
                    if category_name not in categories_cache:
                        category = db.query(Category).filter(Category.name == category_name).first()
                        if not category:
                            from datetime import datetime
                            category = Category(
                                name=category_name,
                                description=f"Auto-created category for {category_name}",
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db.add(category)
                            db.flush()
                        categories_cache[category_name] = category.id
                    
                    category_id = categories_cache[category_name]
                    
                    # Check if channel exists by acestream_id or stream_url
                    if acestream_id:
                        existing = db.query(Channel).filter(
                            Channel.acestream_id == acestream_id
                        ).first()
                    else:
                        existing = db.query(Channel).filter(
                            Channel.stream_url == data["stream_url"]
                        ).first()
                    
                    if not existing:
                        from datetime import datetime
                        channel = Channel(
                            name=data.get("name", "Unknown"),
                            logo_url=data.get("stream_icon", ""),
                            stream_url=data["stream_url"],
                            acestream_id=acestream_id,
                            epg_id=data.get("epg_channel_id", ""),
                            category_id=category_id,
                            is_active=True,
                            is_online=False,  # Will be checked later
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        db.add(channel)
                        channels_added += 1
                        
                        if channels_added % 100 == 0:
                            logger.info(f"Parsed {channels_added} channels...")
                    else:
                        logger.debug(f"Channel already exists: {data.get('name')}")
                            
                except Exception as e:
                    logger.error(f"Error saving channel {data.get('name')}: {e}")
                    continue
        
        # Commit all changes
        try:
            db.commit()
            logger.info(f"Successfully parsed and saved {channels_added} channels")
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            db.rollback()
            return 0
        
        return channels_added


class ImprovedScraperService:
    """Improved scraper service using xtream_api parser"""
    
    def __init__(self, update_interval: int = 3600):
        self.running = False
        self.last_update = 0
        self.update_interval = update_interval
        
    async def start(self):
        """Start scraper service"""
        logger.info("Starting improved scraper service...")
        self.running = True
        
        # Import channels immediately on startup
        logger.info("Running initial channel import...")
        await self.scrape_m3u_sources()
        
    async def stop(self):
        """Stop scraper service"""
        logger.info("Stopping improved scraper service...")
        self.running = False
    
    async def scrape_m3u_sources(self, db: Session = None) -> Dict[str, int]:
        """Scrape all M3U sources from database"""
        if db is None:
            from app.utils.auth import SessionLocal
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
            
        results = {}
        
        try:
            # Get all enabled scraper URLs
            scraper_urls = db.query(ScraperURL).filter(ScraperURL.is_enabled == True).all()
            
            if not scraper_urls:
                logger.warning("No enabled scraper URLs found")
                return results
            
            logger.info(f"Found {len(scraper_urls)} scraper URL(s) to process")
            
            for scraper_url in scraper_urls:
                try:
                    logger.info(f"Scraping: {scraper_url.url}")
                    
                    parser = M3UParser(scraper_url.url)
                    channels_count = await parser.parse_m3u(db)
                    
                    results[scraper_url.url] = channels_count
                    logger.info(f"Scraped {channels_count} channels from {scraper_url.url}")
                    
                    # Update last scraped time
                    from datetime import datetime
                    scraper_url.last_scraped = datetime.now()
                    scraper_url.last_success = datetime.now() if channels_count > 0 else scraper_url.last_success
                    scraper_url.channels_found = channels_count
                    scraper_url.updated_at = datetime.now()
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error scraping {scraper_url.url}: {e}")
                    results[scraper_url.url] = 0
                    continue
            
            self.last_update = int(time.time())
            
        except Exception as e:
            logger.error(f"Error in scrape_m3u_sources: {e}")
        finally:
            if close_db:
                db.close()
        
        return results
    
    async def trigger_scraping(self) -> Dict[str, any]:
        """Manually trigger scraping"""
        logger.info("Manual scraping triggered")
        
        start_time = time.time()
        results = await self.scrape_m3u_sources()
        elapsed = time.time() - start_time
        
        total_channels = sum(results.values())
        
        return {
            "success": True,
            "total_channels": total_channels,
            "sources_processed": len(results),
            "results": results,
            "elapsed_seconds": round(elapsed, 2)
        }
    
    async def auto_scrape_loop(self):
        """Automatic scraping loop"""
        logger.info(f"Auto-scrape loop started (interval: {self.update_interval}s)")
        
        while self.running:
            try:
                # Check if it's time to scrape
                current_time = int(time.time())
                if current_time - self.last_update >= self.update_interval:
                    logger.info("Auto-scrape triggered")
                    await self.scrape_m3u_sources()
                else:
                    # Calculate time until next scrape
                    time_left = self.update_interval - (current_time - self.last_update)
                    logger.debug(f"Next auto-scrape in {time_left}s")
                
                # Sleep for a bit before checking again
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                logger.info("Auto-scrape loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-scrape loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
        
        logger.info("Auto-scrape loop stopped")
