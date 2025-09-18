#!/usr/bin/env python3
"""
Simple API Test Script

This script tests the basic functionality of the YouTube Audio Extractor API.
"""

import asyncio
import httpx
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing YouTube Audio Extractor API")
        print("=" * 50)
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {data['service']} is {data['status']}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Cannot connect to API server: {e}")
            print("   💡 Make sure the server is running: python start_server.py")
            return False
        
        # Test configuration endpoint
        print("\n2. Testing configuration endpoint...")
        try:
            response = await client.get(f"{base_url}/api/audio/config")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Supported formats: {', '.join(data['supported_formats'])}")
                sample_rates = [str(config['sample_rate']) for config in data['sample_rate_configs'].values()]
                print(f"   ✅ Sample rates: {', '.join(sample_rates)}Hz")
            else:
                print(f"   ❌ Config test failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Config test error: {e}")
        
        # Test URL validation with a sample URL
        print("\n3. Testing URL validation...")
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Famous Rick Roll video
        try:
            response = await client.post(
                f"{base_url}/api/audio/validate",
                json={"url": test_url}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    print(f"   ✅ URL validation works: {data.get('title', 'Unknown title')}")
                else:
                    print(f"   ⚠️  URL appears invalid (might be expected)")
            else:
                print(f"   ❌ Validation test failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Validation test error: {e}")
        
        # Test file listing
        print("\n4. Testing file listing...")
        try:
            response = await client.get(f"{base_url}/api/audio/files")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ File listing works: {data['total_count']} files found")
            else:
                print(f"   ❌ File listing failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ File listing error: {e}")
        
        print("\n🎉 API testing completed!")
        print("\n📚 Next steps:")
        print("   • Check the API documentation: http://localhost:8000/docs")
        print("   • Try the API client: python examples/api_client.py")
        print("   • Start extracting audio from YouTube videos!")
        
        return True


def main():
    """Main function."""
    try:
        success = asyncio.run(test_api())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
