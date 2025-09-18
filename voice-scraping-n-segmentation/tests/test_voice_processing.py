#!/usr/bin/env python3
"""
Voice Processing Test Script

This script tests the Khmer voice processing pipeline including VAD, transcription, MFA, and CSV export.
"""

import asyncio
import httpx
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class VoiceProcessingTester:
    """Test class for voice processing functionality."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    async def test_service_status(self, client):
        """Test voice processing service status."""
        print("\n🔍 Testing Voice Processing Service Status...")
        try:
            response = await client.get(f"{self.base_url}/api/voice/status")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ S3 Service: {'Available' if data['s3_service'] else 'Unavailable'}")
                print(f"   ✅ VAD Service: {'Available' if data['vad_service'] else 'Unavailable'}")
                print(f"   ✅ Transcription Service: {'Available' if data['transcription_service'] else 'Unavailable'}")
                print(f"   ✅ MFA Service: {'Available' if data['mfa_service'] else 'Unavailable'}")
                print(f"   ✅ CSV Service: {'Available' if data['csv_service'] else 'Unavailable'}")
                print(f"   ✅ MFA Enabled: {data['use_mfa']}")
                print(f"   ✅ Save Chunks: {data['save_chunks']}")
                return True
            else:
                print(f"   ❌ Service status check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Service status error: {e}")
            return False
    
    async def test_process_local_file(self, client, file_path):
        """Test processing a local audio file."""
        print(f"\n🎙️ Testing Local File Processing: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"   ⚠️  File not found: {file_path}")
            print("   💡 Create a test audio file or use a different path")
            return False
        
        try:
            request_data = {
                "local_file_path": file_path,
                "use_mfa": False,  # Start with MFA disabled for initial testing
                "save_chunks": True,
                "vad_aggressiveness": 2,
                "min_chunk_duration": 1.5,
                "max_chunk_duration": 5.0,
                "transcription_model": "base"
            }
            
            print(f"   📤 Sending request: {json.dumps(request_data, indent=2)}")
            
            response = await client.post(
                f"{self.base_url}/api/voice/process",
                json=request_data,
                timeout=300.0  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                
                print(f"   ✅ Processing successful!")
                print(f"   📋 Session ID: {self.session_id}")
                print(f"   ⏱️  Processing Duration: {data.get('processing_duration', 0):.2f}s")
                
                if 'data' in data:
                    result_data = data['data']
                    print(f"   🔊 Total Chunks: {result_data.get('total_chunks', 0)}")
                    print(f"   📏 Total Duration: {result_data.get('total_duration', 0):.2f}s")
                    print(f"   🎯 Speech Ratio: {result_data.get('speech_ratio', 0):.2%}")
                    print(f"   ✅ Successful Transcriptions: {result_data.get('successful_transcriptions', 0)}")
                    print(f"   ❌ Failed Transcriptions: {result_data.get('failed_transcriptions', 0)}")
                    print(f"   🔤 MFA Alignments: {result_data.get('mfa_alignments', 0)}")
                    print(f"   💾 Saved Chunks: {result_data.get('saved_chunks', 0)}")
                    print(f"   📊 CSV Exported: {result_data.get('csv_exported', False)}")
                
                return True
            else:
                print(f"   ❌ Processing failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 Error details: {error_data}")
                except:
                    print(f"   📝 Response text: {response.text}")
                return False
                
        except asyncio.TimeoutError:
            print(f"   ⏰ Processing timed out (this is normal for long audio files)")
            return False
        except Exception as e:
            print(f"   ❌ Processing error: {e}")
            return False
    
    async def test_process_s3_file(self, client, s3_key):
        """Test processing an S3 audio file."""
        print(f"\n☁️ Testing S3 File Processing: {s3_key}")
        
        try:
            request_data = {
                "s3_key": s3_key,
                "use_mfa": False,
                "save_chunks": True,
                "transcription_model": "base"
            }
            
            response = await client.post(
                f"{self.base_url}/api/voice/process",
                json=request_data,
                timeout=300.0
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                print(f"   ✅ S3 processing successful!")
                print(f"   📋 Session ID: {self.session_id}")
                return True
            else:
                print(f"   ❌ S3 processing failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   📝 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ S3 processing error: {e}")
            return False
    
    async def test_async_processing(self, client, s3_key):
        """Test asynchronous processing."""
        print(f"\n⚡ Testing Async Processing: {s3_key}")
        
        try:
            request_data = {
                "s3_key": s3_key,
                "processing_config": {
                    "use_mfa": False,
                    "save_chunks": True,
                    "transcription_model": "base"
                }
            }
            
            # Start async processing
            response = await client.post(
                f"{self.base_url}/api/voice/process-async",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                print(f"   ✅ Async task started: {task_id}")
                
                # Poll for status
                for i in range(10):  # Check for up to 50 seconds
                    await asyncio.sleep(5)
                    status_response = await client.get(f"{self.base_url}/api/voice/task/{task_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        print(f"   📊 Task status: {status}")
                        
                        if status in ['completed', 'failed']:
                            if status == 'completed':
                                print(f"   ✅ Async processing completed!")
                                return True
                            else:
                                print(f"   ❌ Async processing failed: {status_data.get('error')}")
                                return False
                    else:
                        print(f"   ⚠️  Status check failed: {status_response.status_code}")
                
                print(f"   ⏰ Async processing still running after polling")
                return True
            else:
                print(f"   ❌ Async start failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Async processing error: {e}")
            return False
    
    async def test_session_management(self, client):
        """Test session management endpoints."""
        print(f"\n📋 Testing Session Management...")
        
        try:
            # List sessions
            response = await client.get(f"{self.base_url}/api/voice/sessions")
            if response.status_code == 200:
                data = response.json()
                sessions = data.get('sessions', [])
                print(f"   ✅ Found {len(sessions)} sessions")
                
                if sessions:
                    latest_session = sessions[0]
                    session_id = latest_session.get('session_id')
                    print(f"   📋 Latest session: {session_id}")
                    
                    # Get session details
                    detail_response = await client.get(f"{self.base_url}/api/voice/sessions/{session_id}")
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        if detail_data.get('success'):
                            session_info = detail_data['data']
                            chunks = session_info.get('chunks', [])
                            print(f"   ✅ Session details: {len(chunks)} chunks")
                            
                            # Show first few chunks with Khmer text
                            for i, chunk in enumerate(chunks[:3]):
                                transcription = chunk.get('transcription', 'No transcription')
                                print(f"   📝 Chunk {i+1}: {transcription[:50]}{'...' if len(transcription) > 50 else ''}")
                        else:
                            print(f"   ❌ Session details failed: {detail_data.get('error')}")
                    else:
                        print(f"   ❌ Session details request failed: {detail_response.status_code}")
                
                return True
            else:
                print(f"   ❌ Session listing failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Session management error: {e}")
            return False
    
    async def test_csv_export(self, client):
        """Test CSV export functionality."""
        print(f"\n📊 Testing CSV Export...")
        
        try:
            # Test CSV file listing
            if self.session_id:
                response = await client.get(f"{self.base_url}/api/voice/sessions/{self.session_id}/csv")
                if response.status_code == 200:
                    data = response.json()
                    available_files = data.get('available_files', [])
                    print(f"   ✅ Available CSV files: {len(available_files)}")
                    
                    for file_info in available_files:
                        print(f"   📄 {file_info['type']}: {file_info['filename']}")
                    
                    # Try to download chunks.csv
                    csv_response = await client.get(f"{self.base_url}/api/voice/download/chunks.csv")
                    if csv_response.status_code == 200:
                        csv_content = csv_response.text
                        lines = csv_content.split('\n')
                        print(f"   ✅ Downloaded chunks.csv: {len(lines)} lines")
                        
                        # Show header and first data row
                        if len(lines) >= 2:
                            print(f"   📝 Header: {lines[0]}")
                            if lines[1].strip():
                                print(f"   📝 First row: {lines[1][:100]}{'...' if len(lines[1]) > 100 else ''}")
                    else:
                        print(f"   ⚠️  CSV download failed: {csv_response.status_code}")
                    
                    return True
                else:
                    print(f"   ❌ CSV listing failed: {response.status_code}")
                    return False
            else:
                print(f"   ⚠️  No session ID available for CSV testing")
                return False
                
        except Exception as e:
            print(f"   ❌ CSV export error: {e}")
            return False
    
    async def test_cleanup(self, client):
        """Test cleanup functionality."""
        print(f"\n🧹 Testing Cleanup...")
        
        try:
            response = await client.post(f"{self.base_url}/api/voice/cleanup")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Cleanup successful: {data.get('message')}")
                return True
            else:
                print(f"   ❌ Cleanup failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Cleanup error: {e}")
            return False


async def main():
    """Main test function."""
    print("🇰🇭 Khmer Voice Processing API Test Suite")
    print("=" * 60)
    
    tester = VoiceProcessingTester()
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        # Test basic connectivity
        print("1. Testing API connectivity...")
        try:
            response = await client.get(f"{tester.base_url}/health")
            if response.status_code != 200:
                print(f"❌ API server not responding. Make sure it's running on port 8000")
                print("💡 Start server with: python start_server.py")
                return False
            print("   ✅ API server is running")
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            print("💡 Make sure the server is running: python start_server.py")
            return False
        
        # Run test suite
        tests_passed = 0
        total_tests = 0
        
        # Test service status
        total_tests += 1
        if await tester.test_service_status(client):
            tests_passed += 1
        
        # Test session management
        total_tests += 1
        if await tester.test_session_management(client):
            tests_passed += 1
        
        # Test CSV export
        total_tests += 1
        if await tester.test_csv_export(client):
            tests_passed += 1
        
        # Test cleanup
        total_tests += 1
        if await tester.test_cleanup(client):
            tests_passed += 1
        
        # Test with actual file (if available)
        test_files = [
            "data/temp/test_audio.wav",
            "result/sample.wav",
            "/Users/thun/Desktop/test_khmer_audio.wav"  # Adjust path as needed
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                total_tests += 1
                if await tester.test_process_local_file(client, test_file):
                    tests_passed += 1
                break
        else:
            print(f"\n⚠️  No test audio files found. Create a test file to test processing:")
            for file_path in test_files:
                print(f"   • {file_path}")
        
        # Print summary
        print(f"\n📊 Test Summary")
        print(f"=" * 30)
        print(f"Tests Passed: {tests_passed}/{total_tests}")
        print(f"Success Rate: {tests_passed/total_tests*100:.1f}%" if total_tests > 0 else "No tests run")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed or were skipped")
        
        print(f"\n📚 Next Steps:")
        print(f"   • API Documentation: http://localhost:8000/docs")
        print(f"   • Create test audio files for processing")
        print(f"   • Set up S3 credentials to test S3 functionality")
        print(f"   • Check result/ and data/ directories for output files")
        
        return tests_passed == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        sys.exit(1)
