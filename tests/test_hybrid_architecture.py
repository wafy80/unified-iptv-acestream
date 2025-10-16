#!/usr/bin/env python3
"""
Quick test script to verify hybrid architecture
Tests both FastAPI proxy and aiohttp native streaming
"""
import asyncio
import aiohttp
import sys


async def test_aiohttp_direct():
    """Test direct connection to aiohttp streaming server"""
    print("1. Testing aiohttp direct (port 8001)...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test status endpoint
            async with session.get("http://127.0.0.1:8001/ace/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Status endpoint OK: {data}")
                else:
                    print(f"   ❌ Status endpoint failed: {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    return True


async def test_fastapi_proxy():
    """Test FastAPI proxy to aiohttp"""
    print("2. Testing FastAPI proxy (port 8080)...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test status endpoint via FastAPI
            async with session.get("http://localhost:8080/ace/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Proxy status OK: {data}")
                else:
                    print(f"   ❌ Proxy status failed: {response.status}")
                    return False
            
            # Test stats endpoint
            async with session.get("http://localhost:8080/api/aceproxy/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Stats endpoint OK: {data}")
                else:
                    print(f"   ❌ Stats endpoint failed: {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    return True


async def test_streaming(stream_id: str = None):
    """Test actual streaming if stream_id provided"""
    if not stream_id:
        print("3. Skipping streaming test (no stream_id provided)")
        return True
    
    print(f"3. Testing streaming with id={stream_id}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test via FastAPI proxy
            url = f"http://localhost:8080/ace/getstream?id={stream_id}"
            print(f"   Connecting to {url}...")
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    print(f"   ❌ Stream failed to start: {response.status}")
                    return False
                
                print(f"   ✅ Stream started, reading chunks...")
                
                # Read first few chunks
                chunk_count = 0
                async for chunk in response.content.iter_chunked(8192):
                    chunk_count += 1
                    print(f"   📦 Received chunk {chunk_count} ({len(chunk)} bytes)")
                    
                    if chunk_count >= 5:
                        print(f"   ✅ Streaming works! Received {chunk_count} chunks")
                        break
                
                return True
    except asyncio.TimeoutError:
        print(f"   ❌ Timeout waiting for stream")
        return False
    except Exception as e:
        print(f"   ❌ Streaming failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Hybrid FastAPI + aiohttp Architecture")
    print("=" * 60)
    print()
    
    # Get stream_id from command line if provided
    stream_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    results = []
    
    # Test aiohttp direct
    results.append(await test_aiohttp_direct())
    print()
    
    # Test FastAPI proxy
    results.append(await test_fastapi_proxy())
    print()
    
    # Test streaming if stream_id provided
    results.append(await test_streaming(stream_id))
    print()
    
    # Summary
    print("=" * 60)
    if all(results):
        print("✅ All tests PASSED!")
        print()
        print("Architecture working correctly:")
        print("  • aiohttp streaming server: ✅ Running")
        print("  • FastAPI proxy: ✅ Working")
        if stream_id:
            print("  • Streaming: ✅ Working")
        print()
        print("You can now use the server normally:")
        print(f"  curl http://localhost:8080/ace/getstream?id=YOUR_ID")
        return 0
    else:
        print("❌ Some tests FAILED!")
        print()
        print("Check the following:")
        print("  1. Is the server running? (python3 main.py)")
        print("  2. Is AceStream engine running?")
        print("  3. Check logs in logs/app.log")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
