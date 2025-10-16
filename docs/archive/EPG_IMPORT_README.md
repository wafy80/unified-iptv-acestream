# EPG Management Import from xtream_api

## Overview

This document describes the EPG (Electronic Program Guide) management functionality imported from the `xtream_api` project to enhance the `unified-iptv-acestream` platform.

## Imported Components

### 1. XMLTV Library (`app/utils/xmltv.py`)

Complete Python implementation of the XMLTV format based on XMLTV.pm, providing:

- **Reading XMLTV files**: Parse channels and programmes from XMLTV format
- **Writing XMLTV files**: Generate properly formatted XMLTV output
- **Data structures**: Convert between XMLTV elements and Python dictionaries
- **Standards compliance**: Full support for XMLTV DTD including:
  - Channel information (display names, icons, URLs)
  - Programme data (titles, descriptions, categories, ratings)
  - Credits (actors, directors, producers, etc.)
  - Episode numbering
  - Video/audio metadata
  - Subtitles and ratings

### 2. Enhanced EPG Service (`app/services/epg_service.py`)

The EPG service has been enhanced with methods from xtream_api:

#### New Methods

1. **`download_epg(files: List[str])`**
   - Downloads EPG files from URLs
   - Automatic gzip decompression
   - User-Agent spoofing for compatibility
   - Creates necessary directories

2. **`parse_channel(channel, channels_db)`**
   - Matches XMLTV channels with database channels via `epg_id`
   - Cyrillic character transliteration support
   - Icon extraction from XMLTV data

3. **`parse_programme(programmes)`**
   - Filters programmes for tracked channels
   - Efficient channel ID matching

4. **`write_epg(output_file)`**
   - Generates consolidated XMLTV file
   - Pretty-printed XML output
   - Configurable output location

5. **`parse_xml_files(files: List[str])`**
   - Async parsing of XMLTV files
   - Channel and programme extraction
   - Database updates with icons

6. **`update_epg_with_xmltv()`**
   - Complete XMLTV-based EPG update workflow
   - Downloads from multiple sources
   - Parses and consolidates data
   - Writes output file

7. **`get_short_epg(channel_id, limit=4)`**
   - Xtream API compatible short EPG
   - Returns next N programmes for a channel
   - Formatted for Xtream clients

8. **`get_simple_data_table(channel_id)`**
   - Full EPG data for a channel
   - 7-day programme listings
   - Xtream API format

9. **Enhanced `generate_epg_xml(channel_ids)`**
   - Now uses XMLTV library for proper formatting
   - Full XMLTV compliance
   - Pretty-printed output

## Configuration

The EPG service uses these configuration options:

```python
# EPG Sources (comma-separated URLs)
epg_sources: str = "https://iptvx.one/EPG_NOARCH,https://epg.pw/xmltv/epg.xml.gz"

# Update interval in seconds (default: 24 hours)
epg_update_interval: int = 86400

# Cache file location
epg_cache_file: str = "data/epg.xml"

# Whether EPG files are gzipped
epg_is_gzipped: bool = True
```

## Usage Examples

### Basic EPG Update

```python
from app.services.epg_service import EPGService
from app.database import get_db

# Create service instance
db = next(get_db())
epg_service = EPGService(db)

# Start service
await epg_service.start()

# Update EPG using XMLTV method
programs_count = await epg_service.update_epg_with_xmltv()
print(f"Updated {programs_count} programmes")

# Stop service
await epg_service.stop()
```

### Get EPG for Xtream API

```python
# Get short EPG (next 4 programmes)
short_epg = epg_service.get_short_epg(channel_id=123, limit=4)

# Get full EPG table (7 days)
full_epg = epg_service.get_simple_data_table(channel_id=123)

# Returns:
# {
#     "epg_listings": [
#         {
#             "id": "456",
#             "title": "Programme Title",
#             "start": "2025-10-12 20:00:00",
#             "end": "2025-10-12 21:00:00",
#             "description": "Programme description",
#             "channel_id": "123",
#             "start_timestamp": 1728763200,
#             "stop_timestamp": 1728766800
#         }
#     ]
# }
```

### Generate XMLTV File

```python
# Generate XMLTV for specific channels
xml_content = epg_service.generate_epg_xml(channel_ids=[1, 2, 3])

# Write to file
with open("epg_export.xml", "w") as f:
    f.write(xml_content)
```

## Channel EPG ID Mapping

For EPG to work, channels in the database must have their `epg_id` field set to match the channel ID in the XMLTV source:

```python
# Example channel setup
channel = Channel(
    name="BBC One",
    epg_id="bbc-one.uk",  # Must match XMLTV channel id
    logo_url="https://example.com/bbc-one.png"
)
```

## EPG Data Flow

```
1. Download EPG files from configured sources
   ↓
2. Decompress gzipped files if needed
   ↓
3. Parse XMLTV format using xmltv library
   ↓
4. Match channels via epg_id
   ↓
5. Filter programmes for tracked channels
   ↓
6. Update channel icons if found
   ↓
7. Generate consolidated XMLTV output
   ↓
8. Store in cache file (data/epg.xml)
```

## Key Features Imported

1. **Multiple EPG Source Support**: Download and merge from multiple XMLTV sources
2. **Automatic Decompression**: Handles gzipped XMLTV files automatically
3. **Icon Extraction**: Updates channel logos from EPG data
4. **Cyrillic Support**: Transliterates Cyrillic channel names
5. **XMLTV Compliance**: Full support for XMLTV DTD specification
6. **Xtream API Compatibility**: Get short EPG and data tables in Xtream format
7. **Pretty Printing**: Human-readable XML output
8. **Async Processing**: Non-blocking EPG updates
9. **Error Handling**: Robust error handling for network issues and parsing errors

## Benefits

- **Standards Compliance**: Full XMLTV format support
- **Rich Metadata**: Support for credits, ratings, episodes, etc.
- **Better Client Compatibility**: Many IPTV clients expect XMLTV format
- **Xtream API Support**: Compatible with Xtream API clients
- **Efficient**: Only processes channels tracked in database
- **Flexible**: Multiple EPG sources can be combined

## File Structure

```
unified-iptv-acestream/
├── app/
│   ├── services/
│   │   └── epg_service.py          # Enhanced with xtream_api methods
│   └── utils/
│       └── xmltv.py                # XMLTV library (imported)
├── data/
│   ├── epg/                        # Downloaded EPG files (temp)
│   └── epg.xml                     # Consolidated EPG output
└── EPG_IMPORT_README.md            # This file
```

## Dependencies

- `unidecode`: For Cyrillic character transliteration (already in requirements.txt)
- `aiohttp`: For async HTTP downloads
- `sqlalchemy`: For database operations

## Testing

To test the EPG functionality:

```python
import asyncio
from app.services.epg_service import EPGService
from app.database import get_db

async def test_epg():
    db = next(get_db())
    epg_service = EPGService(db)
    
    await epg_service.start()
    
    # Test XMLTV update
    count = await epg_service.update_epg_with_xmltv()
    print(f"Updated {count} programmes")
    
    # Test short EPG
    short = epg_service.get_short_epg(1, limit=4)
    print(f"Short EPG: {short}")
    
    await epg_service.stop()

asyncio.run(test_epg())
```

## Migration Notes

- All xtream_api EPG functionality is now available in unified-iptv-acestream
- The XMLTV library is standalone and can be updated independently
- Configuration is centralized in `app/config.py`
- EPG updates can be triggered manually or scheduled via the auto-update loop

## Future Enhancements

Potential improvements that could be added:

1. EPG source priority/fallback system
2. Incremental EPG updates (only new programmes)
3. EPG search and filtering API
4. Programme notifications/reminders
5. EPG-based recording scheduler
6. Multi-language EPG support
7. Custom EPG transformations/filters

## Troubleshooting

### EPG Not Updating

1. Check `epg_sources` configuration is set
2. Verify channels have `epg_id` set correctly
3. Check EPG source URLs are accessible
4. Look for errors in logs

### No Programmes Showing

1. Verify channel `epg_id` matches XMLTV source
2. Check EPG source contains data for your channels
3. Ensure programme times are in the future
4. Verify database permissions for EPGProgram table

### Icons Not Updating

1. EPG source must include `<icon>` elements
2. Channel must be matched via `epg_id`
3. Check icon URLs are valid

## Credits

EPG management functionality imported from [xtream_api](../xtream_api) project, which includes:
- XMLTV library based on XMLTV.pm by James Oakley
- EPG parsing and generation utilities
- Xtream API compatibility layer
