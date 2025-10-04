#!/usr/bin/env python3
"""
Khmer Voice Processing Example

This script demonstrates how to use the Khmer voice processing pipeline
to split audio into chunks, transcribe, and export metadata.
"""

import requests
import json
import time
import os
from pathlib import Path


class KhmerVoiceProcessor:
    """Example client for Khmer voice processing."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def check_services(self):
        """Check if all services are available."""
        print("🔍 Checking voice processing services...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/voice/status")
            if response.status_code == 200:
                data = response.json()
                
                print(f"   S3 Service: {'✅' if data['s3_service'] else '❌'}")
                print(f"   VAD Service: {'✅' if data['vad_service'] else '❌'}")
                print(f"   Transcription: {'✅' if data['transcription_service'] else '❌'}")
                print(f"   MFA Service: {'✅' if data['mfa_service'] else '❌'}")
                print(f"   CSV Export: {'✅' if data['csv_service'] else '❌'}")
                
                return data
            else:
                print(f"❌ Service check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            print("💡 Make sure the server is running: python start_server.py")
            return None
    
    def process_audio_file(self, file_path, options=None):
        """
        Process an audio file through the Khmer voice pipeline.
        
        Args:
            file_path: Path to the audio file (local or S3 key)
            options: Processing options
        
        Returns:
            Processing result dictionary
        """
        if options is None:
            options = {}
        
        # Default options optimized for Khmer
        default_options = {
            "use_mfa": False,  # Start with MFA disabled for testing
            "save_chunks": True,
            "vad_aggressiveness": 2,  # Optimized for Khmer
            "min_chunk_duration": 1.5,  # Longer for Khmer sentences
            "max_chunk_duration": 5.0,
            "transcription_model": "base"  # Good balance for Khmer
        }
        default_options.update(options)
        
        # Determine if it's a local file or S3 key
        if os.path.exists(file_path):
            print(f"🎙️ Processing local file: {file_path}")
            request_data = {
                "local_file_path": file_path,
                **default_options
            }
        else:
            print(f"☁️ Processing S3 file: {file_path}")
            request_data = {
                "s3_key": file_path,
                **default_options
            }
        
        try:
            print(f"📤 Sending processing request...")
            print(f"   Settings: VAD={default_options['vad_aggressiveness']}, "
                  f"Chunks={default_options['min_chunk_duration']}-{default_options['max_chunk_duration']}s, "
                  f"Model={default_options['transcription_model']}")
            
            response = self.session.post(
                f"{self.base_url}/api/voice/process",
                json=request_data,
                timeout=300  # 5 minutes
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Processing completed successfully!")
                
                session_id = result.get('session_id')
                processing_time = result.get('processing_duration', 0)
                
                print(f"📋 Session ID: {session_id}")
                print(f"⏱️  Processing Time: {processing_time:.2f}s")
                
                if 'data' in result:
                    data = result['data']
                    print(f"\n📊 Results:")
                    print(f"   🔊 Total Chunks: {data.get('total_chunks', 0)}")
                    print(f"   📏 Total Duration: {data.get('total_duration', 0):.2f}s")
                    print(f"   🎯 Speech Ratio: {data.get('speech_ratio', 0):.2%}")
                    print(f"   ✅ Successful Transcriptions: {data.get('successful_transcriptions', 0)}")
                    print(f"   ❌ Failed Transcriptions: {data.get('failed_transcriptions', 0)}")
                    print(f"   💾 Saved Chunks: {data.get('saved_chunks', 0)}")
                    print(f"   📊 CSV Exported: {data.get('csv_exported', False)}")
                    
                    # Show chunk summaries
                    chunks_summary = data.get('chunks_summary', [])
                    if chunks_summary:
                        print(f"\n📝 First 3 Chunks:")
                        for i, chunk in enumerate(chunks_summary[:3]):
                            transcription = chunk.get('transcription_text', 'No transcription')
                            start_time = chunk.get('start_time', 0)
                            duration = chunk.get('duration', 0)
                            print(f"   {i+1}. {start_time:.1f}s ({duration:.1f}s): {transcription[:80]}{'...' if len(transcription) > 80 else ''}")
                
                return result
            else:
                print(f"❌ Processing failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"📝 Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"📝 Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Request timed out (normal for long audio files)")
            return None
        except Exception as e:
            print(f"❌ Processing error: {e}")
            return None
    
    def get_session_details(self, session_id):
        """Get detailed information about a processing session."""
        print(f"📋 Getting session details: {session_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/api/voice/sessions/{session_id}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result['data']
                    session = data['session']
                    chunks = data['chunks']
                    summary = data['summary']
                    
                    print(f"✅ Session Details:")
                    print(f"   📁 Source: {session.get('source_file', 'Unknown')}")
                    print(f"   🔊 Total Chunks: {len(chunks)}")
                    print(f"   📏 Total Duration: {session.get('total_duration', 0):.2f}s")
                    print(f"   ⏱️  Processing Time: {session.get('processing_duration', 0):.2f}s")
                    print(f"   🇰🇭 Languages: {summary.get('languages_detected', [])}")
                    
                    # Show transcriptions with Khmer text
                    print(f"\n📝 Chunk Transcriptions:")
                    for i, chunk in enumerate(chunks[:5]):  # Show first 5
                        transcription = chunk.get('transcription', 'No transcription')
                        confidence = chunk.get('confidence', 0)
                        print(f"   {i+1}. ({confidence:.2f}) {transcription}")
                    
                    if len(chunks) > 5:
                        print(f"   ... and {len(chunks) - 5} more chunks")
                    
                    return data
                else:
                    print(f"❌ Session details failed: {result.get('error')}")
                    return None
            else:
                print(f"❌ Session request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Session details error: {e}")
            return None
    
    def download_csv_results(self, session_id, output_dir="downloads"):
        """Download CSV results for a session."""
        print(f"📊 Downloading CSV results for session: {session_id}")
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        try:
            # Get available CSV files
            response = self.session.get(f"{self.base_url}/api/voice/sessions/{session_id}/csv")
            
            if response.status_code == 200:
                data = response.json()
                available_files = data.get('available_files', [])
                
                print(f"   Available files: {len(available_files)}")
                
                downloaded_files = []
                for file_info in available_files:
                    file_type = file_info['type']
                    filename = file_info['filename']
                    
                    # Download the file
                    download_response = self.session.get(f"{self.base_url}/api/voice/download/{filename}")
                    
                    if download_response.status_code == 200:
                        output_path = os.path.join(output_dir, f"{session_id}_{filename}")
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(download_response.text)
                        
                        print(f"   ✅ Downloaded {file_type}: {output_path}")
                        downloaded_files.append(output_path)
                    else:
                        print(f"   ❌ Failed to download {filename}: {download_response.status_code}")
                
                return downloaded_files
            else:
                print(f"❌ CSV listing failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ CSV download error: {e}")
            return []
    
    def list_recent_sessions(self, limit=10):
        """List recent processing sessions."""
        print(f"📋 Listing recent sessions (limit: {limit})...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/voice/sessions?limit={limit}")
            
            if response.status_code == 200:
                data = response.json()
                sessions = data.get('sessions', [])
                
                print(f"   Found {len(sessions)} sessions:")
                
                for i, session in enumerate(sessions):
                    session_id = session.get('session_id', 'Unknown')
                    source_file = session.get('source_file', 'Unknown')
                    total_chunks = session.get('total_chunks', 0)
                    created_at = session.get('created_at', 'Unknown')
                    
                    print(f"   {i+1}. {session_id[:8]}... - {total_chunks} chunks - {Path(source_file).name}")
                
                return sessions
            else:
                print(f"❌ Session listing failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Session listing error: {e}")
            return []


def main():
    """Main demonstration function."""
    print("🇰🇭 Khmer Voice Processing Demo")
    print("=" * 50)
    
    # Initialize processor
    processor = KhmerVoiceProcessor()
    
    # Check services
    services = processor.check_services()
    if not services:
        print("❌ Cannot connect to voice processing services")
        return
    
    print("\n" + "="*50)
    print("📋 TESTING OPTIONS")
    print("="*50)
    
    # Test options
    test_files = [
        # Add your test files here
        "data/temp/test_khmer_audio.wav",
        "result/sample_khmer.wav",
        "/Users/thun/Desktop/khmer_test.wav",
        # S3 examples (if you have S3 configured)
        # "audio-files/khmer-speech-01.wav",
    ]
    
    print("Available test options:")
    print("1. Process a local audio file")
    print("2. List recent sessions")
    print("3. View session details")
    print("4. Download CSV results")
    print("\nTest files to try:")
    for i, file_path in enumerate(test_files):
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"   {exists} {file_path}")
    
    print(f"\n💡 To test voice processing:")
    print(f"   1. Create a Khmer audio file (WAV format recommended)")
    print(f"   2. Place it in one of the test file locations")
    print(f"   3. Run this script to process it")
    
    # Auto-test if we find a file
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🎯 Found test file: {test_file}")
            print(f"   Processing automatically...")
            
            # Process the file
            result = processor.process_audio_file(test_file)
            
            if result and result.get('success'):
                session_id = result.get('session_id')
                
                # Get detailed results
                print(f"\n📋 Getting detailed results...")
                session_details = processor.get_session_details(session_id)
                
                # Download CSV
                print(f"\n📊 Downloading CSV results...")
                csv_files = processor.download_csv_results(session_id)
                
                if csv_files:
                    print(f"\n✅ Voice processing demo completed!")
                    print(f"   📁 Results saved to: downloads/")
                    print(f"   📊 CSV files: {len(csv_files)}")
                    print(f"   📋 Session ID: {session_id}")
                else:
                    print(f"\n⚠️  Processing completed but CSV download failed")
            
            break
    else:
        print(f"\n⚠️  No test files found")
        print(f"   Create a test audio file and run again")
    
    # List recent sessions
    print(f"\n📋 Recent sessions:")
    processor.list_recent_sessions(5)
    
    print(f"\n🎉 Demo completed!")
    print(f"📚 Next steps:")
    print(f"   • Check the downloads/ directory for CSV results")
    print(f"   • View API docs: http://localhost:8000/docs")
    print(f"   • Test with your own Khmer audio files")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
