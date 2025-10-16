"""
EPG (Electronic Program Guide) Service
Enhanced with XMLTV library support from xtream_api
"""
import asyncio
import gzip
import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from io import BytesIO
import urllib.request
import urllib.error
import re

import aiohttp
from sqlalchemy.orm import Session
from unidecode import unidecode

from app.models import EPGSource, EPGProgram, Channel
from app.config import get_config
from app.utils import xmltv

logger = logging.getLogger(__name__)

def transliterate(text):
    """
    Transliterate text while preserving the 'live' indicator character (⋗).
    
    :param text: Input text to transliterate
    :return: Transliterated text with live indicator preserved if present
    """

    if text and any("\u0400" <= c <= "\u04FF" for c in text):
        # Text contains Cyrillic characters, proceed with transliteration
        pass
    else:
        # No Cyrillic characters, return original text
        return text

    if text is None:
        return None

    # Check if text is empty or contains only whitespace
    if not text.strip():
        return text

    # Check if the live indicator character exists in the text
    has_live_indicator = "⋗" in text
    if has_live_indicator:
        # Remove all instances of the live indicator character
        text = text.replace("⋗", "").strip()

    # Transliterate the cleaned text
    transliterated_text = unidecode(text)

    # Add back the live indicator at the beginning if it was originally present
    if has_live_indicator:
        transliterated_text = "⋗ " + transliterated_text

    return transliterated_text

class EPGService:
    """Service for managing Electronic Program Guide data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, List[dict]] = {}
        self.epg_channel = []
        self.epg_channel_id = []
        self.epg_program = []
        
        # Configure xmltv settings
        xmltv.locale = "Latin-1"
        xmltv.date_format = "%Y%m%d%H%M%S %Z"
        
    async def start(self):
        """Start EPG service"""
        self.session = aiohttp.ClientSession()
        await self.update_all_epg()  
        logger.info("EPG service started")

    async def stop(self):
        """Stop EPG service"""
        if self.session:
            await self.session.close()
        logger.info("EPG service stopped")
    
    def _get_icon(self, icons=None):
        """
        Get the first icon from the list of icons.
        
        :param icons: List of dictionaries containing icon sources
        :return: Icon URL or None
        """
        if not icons:
            return None
        chanel_icon = icons[0]["src"]
        # if icon count is more than 1
        if len(icons) > 1:
            for icon in icons:
                chanel_icon = icon["src"]
                break
        return chanel_icon
                
    def clean_duplicate_programs(self, channel_id: Optional[int] = None) -> int:
        """
        Clean duplicate EPG programs from database
        
        :param channel_id: Optional channel ID to clean, or None for all channels
        :return: Number of duplicates removed
        """
        removed_count = 0
        
        try:
            # Get channels to process
            if channel_id:
                channels = [self.db.query(Channel).filter(Channel.id == channel_id).first()]
            else:
                channels = self.db.query(Channel).all()
            
            for channel in channels:
                if not channel:
                    continue
                
                # Get all programs for this channel
                programs = self.db.query(EPGProgram).filter(
                    EPGProgram.channel_id == channel.id
                ).order_by(EPGProgram.start_time).all()
                
                # Track seen programmes
                seen = set()
                duplicates = []
                
                for program in programs:
                    # Create key: start_time (rounded to minute) + title
                    key = (
                        program.start_time.replace(second=0, microsecond=0),
                        program.title.strip()
                    )
                    
                    if key in seen:
                        # This is a duplicate
                        duplicates.append(program.id)
                    else:
                        seen.add(key)
                
                # Delete duplicates
                if duplicates:
                    self.db.query(EPGProgram).filter(
                        EPGProgram.id.in_(duplicates)
                    ).delete(synchronize_session=False)
                    removed_count += len(duplicates)
                    logger.info(f"Removed {len(duplicates)} duplicate programs from channel {channel.name}")
            
            self.db.commit()
            logger.info(f"Total duplicates removed: {removed_count}")
            
        except Exception as e:
            logger.error(f"Error cleaning duplicate programs: {e}")
            self.db.rollback()
        
        return removed_count
    
    async def fetch_epg_xml(self, url: str, is_gzipped: bool = True) -> Optional[str]:
        """Fetch EPG XML from URL"""
        logger.info(f"Fetching EPG from {url}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=120)
            
            async with self.session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch EPG: HTTP {response.status}")
                    return None
                
                content = await response.read()
                
                # Decompress if needed
                if is_gzipped:
                    try:
                        content = gzip.decompress(content)
                    except Exception as e:
                        logger.warning(f"Failed to decompress, trying as plain text: {e}")
                
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Error fetching EPG from {url}: {e}")
            return None
    
    def parse_xmltv_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse XMLTV timestamp with timezone support
        Format: YYYYMMDDHHmmss +ZZZZ or YYYYMMDDHHmmss
        
        Examples:
        - 20251013120000 +0300 -> 2025-10-13 12:00:00+03:00 -> converted to UTC
        - 20251013120000 -> 2025-10-13 12:00:00 UTC
        
        :param timestamp_str: XMLTV timestamp string
        :return: datetime object in UTC or None if parsing fails
        """
        try:
            # XMLTV format: YYYYMMDDHHmmss +ZZZZ or YYYYMMDDHHmmss
            # Extract the date/time part (first 14 chars)
            dt_part = timestamp_str[:14].strip()
            
            # Extract timezone if present (after position 14)
            tz_part = timestamp_str[14:].strip()
            
            # Parse base datetime
            dt = datetime.strptime(dt_part, '%Y%m%d%H%M%S')
            
            if tz_part:
                # Parse timezone offset
                # Format can be: +0300, +03:00, +03, etc.
                tz_match = re.match(r'([+-])(\d{2}):?(\d{2})?', tz_part)
                if tz_match:
                    sign = 1 if tz_match.group(1) == '+' else -1
                    hours = int(tz_match.group(2))
                    minutes = int(tz_match.group(3) or '0')
                    
                    # Create timezone-aware datetime
                    offset = timedelta(hours=sign * hours, minutes=sign * minutes)
                    tz = timezone(offset)
                    dt = dt.replace(tzinfo=tz)
                    
                    # Convert to UTC
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    # No valid timezone found, assume UTC
                    pass
            else:
                # No timezone specified, assume UTC
                pass
            
            return dt
            
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None
    
    def parse_epg_xml(self, xml_content: str, valid_epg_ids: set = None) -> Dict[str, List[dict]]:
        """
        Parse EPG XML and return programs by channel
        
        :param xml_content: XML content to parse
        :param valid_epg_ids: Optional set of valid EPG IDs to filter during parsing
        :return: Dictionary of programs by channel
        """
        programs_by_channel = {}
        
        # Define time window for EPG programs (only save relevant events)
        # Use naive datetime (no timezone) since parsed times are also naive
        now = datetime.utcnow()
        past_window = now - timedelta(days=1)  # Keep last 1 day for catch-up
        future_window = now + timedelta(days=7)  # Keep next 7 days
        
        try:
            root = ET.fromstring(xml_content)
            
            # First pass: get channel mappings (optional, for reference)
            channel_map = {}
            for channel_elem in root.findall('.//channel'):
                channel_id = channel_elem.get('id')
                display_name = channel_elem.find('display-name')
                if channel_id and display_name is not None:
                    channel_map[channel_id] = display_name.text
            
            # Second pass: get programs (filter during parsing if valid_epg_ids provided)
            skipped_count = 0
            old_events_skipped = 0
            for programme in root.findall('.//programme'):
                channel_id = programme.get('channel')
                start = programme.get('start')
                stop = programme.get('stop')
                
                if not all([channel_id, start, stop]):
                    continue
                
                # Skip if valid_epg_ids provided and this channel is not in it
                if valid_epg_ids is not None and channel_id not in valid_epg_ids:
                    skipped_count += 1
                    continue
                
                # Parse datetime with timezone support
                start_dt = self.parse_xmltv_timestamp(start)
                stop_dt = self.parse_xmltv_timestamp(stop)
                
                if not start_dt or not stop_dt:
                    continue
                
                # Skip old events (ended before past_window) and too far future events
                if stop_dt < past_window or start_dt > future_window:
                    old_events_skipped += 1
                    continue
                
                # Extract program data
                title_elem = programme.find('title')
                desc_elem = programme.find('desc')
                category_elem = programme.find('category')
                icon_elem = programme.find('icon')
                rating_elem = programme.find('rating')
                
                program_data = {
                    'epg_id': channel_id,
                    'title': transliterate(title_elem.text) if title_elem is not None else 'Unknown',
                    'description': transliterate(desc_elem.text) if desc_elem is not None else None,
                    'start_time': start_dt,
                    'end_time': stop_dt,
                    'category': category_elem.text if category_elem is not None else None,
                    'icon_url': icon_elem.get('src') if icon_elem is not None else None,
                    'rating': rating_elem.find('value').text if rating_elem is not None and rating_elem.find('value') is not None else None
                }
                
                if channel_id not in programs_by_channel:
                    programs_by_channel[channel_id] = []
                
                programs_by_channel[channel_id].append(program_data)
            
            if skipped_count > 0:
                logger.info(f"Skipped {skipped_count} programs for non-existent channels during XML parsing")
            if old_events_skipped > 0:
                logger.info(f"Skipped {old_events_skipped} old/future events outside time window")
        
        except Exception as e:
            logger.error(f"Error parsing EPG XML: {e}")
        
        return programs_by_channel
    
    async def update_epg_from_source(self, source: EPGSource) -> int:
        """Update EPG from a single source"""
        logger.info(f"Updating EPG from {source.url}")
        
        try:
            # Fetch XML
            xml_content = await self.fetch_epg_xml(source.url, source.is_gzipped)
            
            if not xml_content:
                source.last_error = "Failed to fetch EPG"
                return 0
            
            # Get all valid epg_ids from database first
            valid_channels = self.db.query(Channel).filter(Channel.epg_id.isnot(None)).all()
            valid_epg_ids = {channel.epg_id for channel in valid_channels}
            
            logger.info(f"Found {len(valid_epg_ids)} channels with EPG IDs in database")
            
            # Parse XML with filtering during parsing
            programs_by_channel = self.parse_epg_xml(xml_content, valid_epg_ids)
            
            logger.info(f"Parsed EPG data for {len(programs_by_channel)} channels")
            
            total_programs = 0
            
            # Update database
            for epg_id, programs in programs_by_channel.items():
                # Find matching channels
                channels = self.db.query(Channel).filter(Channel.epg_id == epg_id).all()
                
                for channel in channels:
                    # Delete ALL existing programs for this channel
                    # This ensures clean slate and prevents duplicates
                    deleted_count = self.db.query(EPGProgram).filter(
                        EPGProgram.channel_id == channel.id
                    ).delete()
                    
                    logger.debug(f"Deleted {deleted_count} existing programs for channel {channel.name}")
                    
                    # Add new programs from EPG source
                    for program_data in programs:
                        start_time = program_data['start_time']
                        end_time = program_data['end_time']
                        title = program_data['title']
                        
                        # Add program (no duplicate check needed since we deleted all)
                        program = EPGProgram(
                            channel_id=channel.id,
                            title=title,
                            description=program_data['description'],
                            start_time=start_time,
                            end_time=end_time,
                            category=program_data['category'],
                            icon_url=program_data['icon_url'],
                            rating=program_data['rating']
                        )
                        self.db.add(program)
                        total_programs += 1

            source.last_updated = datetime.utcnow()
            source.last_success = datetime.utcnow()
            source.programs_found = total_programs
            source.last_error = None
            
            self.db.commit()
            
            logger.info(f"Updated {total_programs} programs from {source.url}")
            return total_programs
            
        except Exception as e:
            logger.error(f"Error updating EPG from {source.url}: {e}")
            source.last_error = str(e)
            self.db.commit()
            return 0
    
    async def update_all_epg(self) -> int:
        """Update EPG from all sources"""
        logger.info("Updating EPG from all sources")
        
        sources = self.db.query(EPGSource).filter(EPGSource.is_enabled == True).all()
        
        total_programs = 0
        for source in sources:
            programs = await self.update_epg_from_source(source)
            total_programs += programs
        
        logger.info(f"EPG update completed: {total_programs} total programs")
        return total_programs
    
    async def auto_update_loop(self):
        """
        Automatic EPG update loop
        Uses XMLTV method if sources are configured, otherwise falls back to database sources
        """
        while True:
            try:
                # Get update interval from config
                interval = self.config.epg_update_interval
                await asyncio.sleep(interval)
                logger.info("Auto EPG update triggered")
                
                # Check if XMLTV sources are configured
                xmltv_sources = self.config.get_epg_sources_list()
                
                if xmltv_sources:
                    # Use XMLTV update method (xtream_api style)
                    logger.info("Using XMLTV update method")
                    programs_count = await self.update_all_epg()
                    logger.info(f"XMLTV EPG update completed: {programs_count} programmes")
                else:
                    logger.info("No XMLTV sources configured, skipping EPG update")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto EPG update loop: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Wait a bit before retrying on error
                await asyncio.sleep(300)  # 5 minutes
    
    def get_programs(self, channel_id: int, hours: int = 24) -> List[EPGProgram]:
        """
        Get programs for a channel for the next N hours
        Includes current program if still running
        """
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)
        
        return self.db.query(EPGProgram).filter(
            EPGProgram.channel_id == channel_id,
            EPGProgram.end_time >= now,  # Include current program (still running)
            EPGProgram.start_time < end_time
        ).order_by(EPGProgram.start_time).all()
    
    def get_short_epg(self, channel_id: int, limit: int = 4) -> Dict:
        """
        Get short EPG for a specific channel (Xtream API compatible)
        Includes current program if still running
        
        :param channel_id: The channel ID
        :param limit: Number of EPG entries to return
        :return: Dictionary with epg_listings
        """
        try:
            now = datetime.utcnow()
            programs = self.db.query(EPGProgram).filter(
                EPGProgram.channel_id == channel_id,
                EPGProgram.end_time >= now  # Include current program
            ).order_by(EPGProgram.start_time).limit(limit).all()
            
            epg_listings = []
            for program in programs:
                epg_listings.append({
                    "id": str(program.id),
                    "epg_id": str(program.id),
                    "title": program.title,
                    "lang": "",
                    "start": program.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": program.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "description": program.description or "",
                    "channel_id": str(channel_id),
                    "start_timestamp": int(program.start_time.timestamp()),
                    "stop_timestamp": int(program.end_time.timestamp()),
                    "has_archive": 0
                })
            
            return {"epg_listings": epg_listings}
            
        except Exception as e:
            logger.error(f"Error getting short EPG for channel {channel_id}: {e}")
            return {"epg_listings": []}
    
    def get_simple_data_table(self, channel_id: int) -> Dict:
        """
        Get full EPG data table for a specific channel (Xtream API compatible)
        Includes current program if still running
        
        :param channel_id: The channel ID
        :return: Dictionary with EPG data
        """
        try:
            now = datetime.utcnow()
            end_time = now + timedelta(days=7)
            
            programs = self.db.query(EPGProgram).filter(
                EPGProgram.channel_id == channel_id,
                EPGProgram.end_time >= now,  # Include current program
                EPGProgram.start_time < end_time
            ).order_by(EPGProgram.start_time).all()
            
            epg_listings = []
            for program in programs:
                epg_listings.append({
                    "id": str(program.id),
                    "epg_id": str(program.id),
                    "title": program.title,
                    "lang": "",
                    "start": program.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": program.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "description": program.description or "",
                    "channel_id": str(channel_id),
                    "start_timestamp": int(program.start_time.timestamp()),
                    "stop_timestamp": int(program.end_time.timestamp()),
                    "has_archive": 0
                })
            
            return {"epg_listings": epg_listings}
            
        except Exception as e:
            logger.error(f"Error getting EPG data for channel {channel_id}: {e}")
            return {"epg_listings": []}
    
    def get_current_program(self, channel_id: int) -> Optional[EPGProgram]:
        """Get current program for a channel"""
        now = datetime.utcnow()
        return self.db.query(EPGProgram).filter(
            EPGProgram.channel_id == channel_id,
            EPGProgram.start_time <= now,
            EPGProgram.end_time > now
        ).first()
    
    def generate_epg_xml(self, channel_ids: Optional[List[int]] = None) -> str:
        """
        Generate EPG XML for specified channels using xmltv library
        
        :param channel_ids: Optional list of channel IDs to generate EPG for
        :return: XML string
        """
        import tempfile
        from zoneinfo import ZoneInfo
        
        # Get server timezone from config
        try:
            server_tz = ZoneInfo(self.config.server_timezone)
        except Exception as e:
            logger.warning(f"Invalid timezone '{self.config.server_timezone}', using UTC: {e}")
            server_tz = timezone.utc
        
        # Generate date format with timezone
        now_with_tz = datetime.now(server_tz)
        date = now_with_tz.strftime("%Y%m%d%H%M%S %z")
        
        # Create an XMLTV writer object
        w = xmltv.Writer(
            encoding="utf-8",
            date=date,
            generator_info_name="unified-iptv-acestream",
            generator_info_url="https://github.com/unified-iptv-acestream",
        )
        
        # Get channels
        query = self.db.query(Channel)
        if channel_ids:
            query = query.filter(Channel.id.in_(channel_ids))
        channels = query.all()
        
        # Add channel elements
        for channel in channels:
            if channel.epg_id:
                channel_data = {
                    "id": channel.epg_id,
                    "display-name": [{"name": channel.name, "lang": ""}]
                }
                
                if channel.logo_url:
                    channel_data["icon"] = [{"src": channel.logo_url}]
                
                w.addChannel(channel_data)
        
        # Add programme elements
        now = datetime.utcnow()
        
        # Include programs that are still running (end_time in future)
        # Also include recent past programs (last 1 day) for catch-up/replay
        past_window = now - timedelta(days=1)  # Keep last 1 day for catch-up
        future_window = now + timedelta(days=7)
        
        # Track added programmes to avoid duplicates in XML output
        added_programmes = set()
        
        for channel in channels:
            programs = self.db.query(EPGProgram).filter(
                EPGProgram.channel_id == channel.id,
                EPGProgram.end_time >= past_window,  # Include recent past + current programs
                EPGProgram.start_time < future_window  # Up to 7 days in future
            ).order_by(EPGProgram.start_time).all()
            
            for program in programs:
                # Create unique key for deduplication
                # Use channel_epg_id, start_time, and title
                prog_key = (
                    channel.epg_id or str(channel.id),
                    program.start_time,
                    program.title
                )
                
                # Skip if already added (duplicate)
                if prog_key in added_programmes:
                    logger.debug(f"Skipping duplicate programme: {program.title} at {program.start_time}")
                    continue
                
                added_programmes.add(prog_key)
                
                # Convert UTC times from database to server timezone for XMLTV
                # Programs are stored in UTC in database
                start_utc = program.start_time.replace(tzinfo=timezone.utc)
                stop_utc = program.end_time.replace(tzinfo=timezone.utc)
                
                # Convert to server timezone
                start_local = start_utc.astimezone(server_tz)
                stop_local = stop_utc.astimezone(server_tz)
                
                # Format with timezone offset
                start_str = start_local.strftime('%Y%m%d%H%M%S %z')
                stop_str = stop_local.strftime('%Y%m%d%H%M%S %z')
                
                programme_data = {
                    "channel": channel.epg_id or str(channel.id),
                    "start": start_str,
                    "stop": stop_str,
                    "title": [{"name": transliterate(program.title), "lang": ""}]
                }
                
                if program.description:
                    programme_data["desc"] = [{"name": transliterate(program.description), "lang": ""}]

                if program.category:
                    programme_data["category"] = [{"name": program.category, "lang": ""}]
                
                if program.icon_url:
                    programme_data["icon"] = [{"src": program.icon_url}]
                
                w.addProgramme(programme_data)
        
        # Generate XML string using temporary file
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xml', delete=True) as tmp:
            w.write(tmp.name, pretty_print=True)
            tmp.seek(0)
            xml_content = tmp.read().decode('utf-8')
        
        return xml_content
