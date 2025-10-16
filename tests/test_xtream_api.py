#!/usr/bin/env python3
"""
Quick test script to verify Xtream API implementation
"""
import asyncio
import aiohttp

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"


async def test_player_api():
    """Test player_api.php endpoint"""
    print("Testing player_api.php...")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/player_api.php?username={USERNAME}&password={PASSWORD}"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ player_api.php OK")
                print(f"  User: {data.get('user_info', {}).get('username')}")
                print(f"  Server: {data.get('server_info', {}).get('url')}")
                return True
            else:
                print(f"✗ player_api.php FAILED: {response.status}")
                return False


async def test_get_live_categories():
    """Test get_live_categories action"""
    print("\nTesting get_live_categories...")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_categories"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ get_live_categories OK - {len(data)} categories")
                for cat in data[:3]:
                    print(f"  - {cat.get('category_name')} (ID: {cat.get('category_id')})")
                return True
            else:
                print(f"✗ get_live_categories FAILED: {response.status}")
                return False


async def test_get_live_streams():
    """Test get_live_streams action"""
    print("\nTesting get_live_streams...")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✓ get_live_streams OK - {len(data)} channels")
                for ch in data[:3]:
                    print(f"  - {ch.get('name')} (ID: {ch.get('stream_id')})")
                return True
            else:
                print(f"✗ get_live_streams FAILED: {response.status}")
                return False


async def test_m3u_playlist():
    """Test M3U playlist generation"""
    print("\nTesting M3U playlist...")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/get.php?username={USERNAME}&password={PASSWORD}&type=m3u_plus"
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                lines = content.split('\n')
                print(f"✓ M3U playlist OK - {len(lines)} lines")
                
                # Count channels
                extinf_count = sum(1 for line in lines if line.startswith('#EXTINF'))
                print(f"  - {extinf_count} channels")
                
                # Check if using /live/ prefix
                live_count = sum(1 for line in lines if '/live/' in line)
                if live_count > 0:
                    print(f"  - ✓ Using /live/ prefix ({live_count} URLs)")
                else:
                    print(f"  - ✗ NOT using /live/ prefix")
                
                return True
            else:
                print(f"✗ M3U playlist FAILED: {response.status}")
                return False


async def test_stream_endpoint():
    """Test streaming endpoint (just check if it responds)"""
    print("\nTesting stream endpoint...")
    
    async with aiohttp.ClientSession() as session:
        # First get a channel ID
        url = f"{BASE_URL}/player_api.php?username={USERNAME}&password={PASSWORD}&action=get_live_streams"
        async with session.get(url) as response:
            if response.status == 200:
                channels = await response.json()
                if channels:
                    stream_id = channels[0]['stream_id']
                    
                    # Try to stream (just check headers, don't download)
                    stream_url = f"{BASE_URL}/live/{USERNAME}/{PASSWORD}/{stream_id}.ts"
                    async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=5)) as stream_response:
                        if stream_response.status in [200, 302, 404]:  # 404 is ok if no stream available
                            print(f"✓ Stream endpoint responding: {stream_response.status}")
                            if stream_response.status == 200:
                                print(f"  - Content-Type: {stream_response.headers.get('content-type')}")
                            return True
                        else:
                            print(f"✗ Stream endpoint FAILED: {stream_response.status}")
                            return False
                else:
                    print("  - No channels available to test")
                    return True
            else:
                print(f"✗ Could not get channels: {response.status}")
                return False


async def test_xmltv():
    """Test XMLTV EPG"""
    print("\nTesting XMLTV EPG...")
    
    async with aiohttp.ClientSession() as session:
        url = f"{BASE_URL}/xmltv.php?username={USERNAME}&password={PASSWORD}"
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                if content.startswith('<?xml'):
                    print(f"✓ XMLTV EPG OK - {len(content)} bytes")
                    return True
                else:
                    print(f"✗ XMLTV EPG invalid format")
                    return False
            else:
                print(f"✗ XMLTV EPG FAILED: {response.status}")
                return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Xtream API Test Suite")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(await test_player_api())
        results.append(await test_get_live_categories())
        results.append(await test_get_live_streams())
        results.append(await test_m3u_playlist())
        results.append(await test_stream_endpoint())
        results.append(await test_xmltv())
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All tests PASSED!")
    else:
        print("✗ Some tests FAILED")


if __name__ == "__main__":
    asyncio.run(main())
