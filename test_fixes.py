#!/usr/bin/env python3
"""
Test script to verify all fixes are working correctly.
This can be run to validate the changes without starting the full application.
"""

import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_config_loading():
    """Test that config loads correctly with SERVER_HOST=0.0.0.0"""
    print("Test 1: Config Loading")
    print("-" * 60)
    
    from app.config import get_config
    
    config = get_config()
    assert config.server_host == "0.0.0.0", "SERVER_HOST should be 0.0.0.0"
    assert config.server_port == 6880, "SERVER_PORT should be 6880"
    
    print(f"✓ SERVER_HOST: {config.server_host}")
    print(f"✓ SERVER_PORT: {config.server_port}")
    print(f"✓ ACESTREAM_ENGINE_PORT: {config.acestream_engine_port}")
    print()


def test_get_base_url():
    """Test that get_base_url handles 0.0.0.0 correctly"""
    print("Test 2: get_base_url() Function")
    print("-" * 60)
    
    from unittest.mock import MagicMock
    from app.api.xtream import get_base_url
    
    # Test case 1: SERVER_HOST=0.0.0.0 with Host header
    print("Test 2.1: 0.0.0.0 with Host header")
    request = MagicMock()
    request.headers = {"host": "192.168.100.130:6880"}
    request.url.hostname = "192.168.100.130"
    request.url.netloc = "192.168.100.130:6880"
    request.url.scheme = "http"
    
    result = get_base_url(request)
    expected = "http://192.168.100.130:6880"
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  Input: SERVER_HOST=0.0.0.0, Host: 192.168.100.130:6880")
    print(f"  ✓ Output: {result}")
    print()
    
    # Test case 2: With forwarded headers (reverse proxy)
    print("Test 2.2: Reverse proxy headers")
    request2 = MagicMock()
    request2.headers = {
        "x-forwarded-host": "example.com",
        "x-forwarded-proto": "https"
    }
    
    result2 = get_base_url(request2)
    expected2 = "https://example.com"
    assert result2 == expected2, f"Expected {expected2}, got {result2}"
    print(f"  Input: x-forwarded-host=example.com, x-forwarded-proto=https")
    print(f"  ✓ Output: {result2}")
    print()
    
    # Test case 3: 0.0.0.0 without Host header
    print("Test 2.3: 0.0.0.0 using request.url")
    request3 = MagicMock()
    request3.headers = {}
    request3.url.hostname = "10.0.0.5"
    request3.url.netloc = "10.0.0.5:6880"
    request3.url.scheme = "http"
    
    result3 = get_base_url(request3)
    expected3 = "http://10.0.0.5:6880"
    assert result3 == expected3, f"Expected {expected3}, got {result3}"
    print(f"  Input: SERVER_HOST=0.0.0.0, request.url=10.0.0.5:6880")
    print(f"  ✓ Output: {result3}")
    print()


def test_playlist_route():
    """Test that /playlist.m3u route is registered"""
    print("Test 3: /playlist.m3u Route Registration")
    print("-" * 60)
    
    from app.api import xtream
    
    routes = [route.path for route in xtream.router.routes]
    
    assert any('/playlist.m3u' in route.path for route in xtream.router.routes), \
        "Route /playlist.m3u not found!"
    
    print("Registered routes:")
    for route in xtream.router.routes:
        if 'playlist' in route.path.lower() or 'get.php' in route.path:
            print(f"  ✓ {route.path}")
    print()


def test_docker_compose():
    """Test that docker-compose.yml has correct volumes"""
    print("Test 4: Docker Compose Configuration")
    print("-" * 60)
    
    import yaml
    
    with open('docker-compose.yml', 'r') as f:
        compose_config = yaml.safe_load(f)
    
    unified_iptv = compose_config['services']['unified-iptv']
    volumes = unified_iptv['volumes']
    
    # Check for required volumes
    volume_targets = [v.split(':')[1] for v in volumes]
    
    assert '/app/data' in volume_targets, "Missing /app/data volume"
    assert '/app/logs' in volume_targets, "Missing /app/logs volume"
    assert '/app/.env' in volume_targets, "Missing /app/.env volume"
    
    print("Configured volumes:")
    for volume in volumes:
        print(f"  ✓ {volume}")
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("VALIDATION TESTS FOR UNIFIED IPTV ACESTREAM FIXES")
    print("=" * 60 + "\n")
    
    try:
        test_config_loading()
        test_get_base_url()
        test_playlist_route()
        test_docker_compose()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ Configuration loads correctly")
        print("  ✓ get_base_url() handles 0.0.0.0 properly")
        print("  ✓ /playlist.m3u endpoint is registered")
        print("  ✓ docker-compose.yml has all required volumes")
        print()
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("✗ TEST FAILED!")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
