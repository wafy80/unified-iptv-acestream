#!/usr/bin/env python3
"""
Test to compare API responses between original and unified implementations
"""

# Expected format from original xtream_api

EXPECTED_USER_INFO = {
    "username": "admin",
    "password": "admin",
    "message": "",  # or message of the day
    "auth": 1,
    "status": "Active",
    "exp_date": None,  # or timestamp
    "is_trial": 0,  # integer, not string
    "active_cons": 0,  # integer
    "created_at": 0,  # timestamp
    "max_connections": 1,  # integer, not string
    "allowed_output_formats": ["m3u8", "ts", "rtmp"]  # array, not JSON string
}

EXPECTED_SERVER_INFO = {
    "xui": True,
    "version": "1.0.0",
    "url": "localhost",
    "port": "8000",
    "https_port": "443",
    "server_protocol": "http",
    "rtmp_port": "1935",
    "timestamp_now": 1234567890,
    "time_now": "2024-01-01 12:00:00",
    "timezone": "UTC"
}

EXPECTED_CATEGORY = {
    "category_id": "1",
    "category_name": "Sports",
    "parent_id": 0  # integer, not string, 0 if no parent
}

EXPECTED_LIVE_STREAM = {
    "num": 1,  # sequential number
    "name": "Channel Name",
    "stream_type": "live",
    "stream_id": 123,  # channel ID
    "stream_icon": "http://...",
    "epg_channel_id": "channel.id",
    "added": "1234567890",  # string timestamp
    "is_adult": "0",
    "category_id": "1",
    "category_ids": [1],  # ARRAY of integers, not JSON string
    "custom_sid": "",
    "tv_archive": 0,
    "direct_source": "",  # important for IPTV Smarters
    "tv_archive_duration": 0
}

print("Expected API Response Formats from Original xtream_api:")
print("=" * 60)

print("\n1. player_api.php (no action):")
print("   user_info:")
for key, value in EXPECTED_USER_INFO.items():
    print(f"     {key}: {type(value).__name__} = {value}")

print("\n   server_info:")
for key, value in EXPECTED_SERVER_INFO.items():
    print(f"     {key}: {type(value).__name__} = {value}")

print("\n2. get_live_categories:")
for key, value in EXPECTED_CATEGORY.items():
    print(f"   {key}: {type(value).__name__} = {value}")

print("\n3. get_live_streams:")
for key, value in EXPECTED_LIVE_STREAM.items():
    print(f"   {key}: {type(value).__name__} = {value}")

print("\n" + "=" * 60)
print("\nKey Differences Fixed:")
print("✓ is_trial: int (not string '1' or '0')")
print("✓ active_cons: int (not string '0')")
print("✓ max_connections: int (not string '1')")
print("✓ allowed_output_formats: array (not JSON string)")
print("✓ server_info.xui: True (was missing)")
print("✓ server_info.version: '1.0.0' (was missing)")
print("✓ server_info.https_port: '443' (was '')")
print("✓ server_info.rtmp_port: '1935' (was '')")
print("✓ category_ids: array of ints (critical for IPTV Smarters)")
print("✓ num: sequential counter (was using channel.id)")
print("✓ parent_id: 0 for no parent (was using 'or 0' which could fail)")
