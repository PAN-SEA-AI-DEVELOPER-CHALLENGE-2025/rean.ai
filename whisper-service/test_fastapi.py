#!/usr/bin/env python3
"""
Test script for Dual-Language Transcription Service - FastAPI Version
Tests both English (Whisper) and Khmer (MMS) transcription endpoints
"""

import requests
import json
import wave
import numpy as np
import tempfile
import os

def create_test_audio():
    """Create a simple test audio file with a known phrase."""
    # Generate a simple sine wave (beep sound)
    # Note: This won't produce recognizable speech, but it will test the pipeline
    sample_rate = 44100
    duration = 2  # seconds
    frequency = 440  # Hz (A note)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return temp_file.name

def test_health_endpoint(base_url):
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_english_transcription(base_url, audio_file):
    """Test the English transcription endpoint."""
    print("Testing English transcription endpoint...")
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            data = {'task': 'transcribe'}
            
            response = requests.post(f"{base_url}/transcribe/english", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ English transcription successful")
                print(f"Text: {result.get('text', 'No text returned')}")
                print(f"Model: {result.get('model', 'Unknown')}")
                print(f"Language: {result.get('language', 'Unknown')}")
                return True
            else:
                print(f"❌ English transcription failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ English transcription error: {e}")
        return False

def test_khmer_transcription(base_url, audio_file):
    """Test the Khmer transcription endpoint."""
    print("Testing Khmer transcription endpoint...")
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            
            response = requests.post(f"{base_url}/transcribe/khmer", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Khmer transcription successful")
                print(f"Text: {result.get('text', 'No text returned')}")
                print(f"Model: {result.get('model', 'Unknown')}")
                print(f"Language: {result.get('language', 'Unknown')}")
                return True
            else:
                print(f"❌ Khmer transcription failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Khmer transcription error: {e}")
        return False

def test_legacy_transcription(base_url, audio_file):
    """Test the legacy transcription endpoint."""
    print("Testing legacy transcription endpoint...")
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            
            response = requests.post(f"{base_url}/transcribe", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Legacy transcription successful")
                print(f"Text: {result.get('text', 'No text returned')}")
                print(f"Model: {result.get('model', 'Unknown')}")
                return True
            else:
                print(f"❌ Legacy transcription failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Legacy transcription error: {e}")
        return False

def test_models_endpoint(base_url):
    """Test the models endpoint."""
    print("Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/models")
        if response.status_code == 200:
            print("✅ Models endpoint successful")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False

def test_docs_endpoints(base_url):
    """Test the automatic documentation endpoints."""
    print("Testing documentation endpoints...")
    try:
        # Test /docs
        docs_response = requests.get(f"{base_url}/docs")
        docs_ok = docs_response.status_code == 200
        
        # Test /redoc
        redoc_response = requests.get(f"{base_url}/redoc")
        redoc_ok = redoc_response.status_code == 200
        
        # Test OpenAPI spec
        openapi_response = requests.get(f"{base_url}/openapi.json")
        openapi_ok = openapi_response.status_code == 200
        
        if docs_ok and redoc_ok and openapi_ok:
            print("✅ Documentation endpoints successful")
            print(f"  📚 Swagger UI: {base_url}/docs")
            print(f"  📖 ReDoc: {base_url}/redoc")
            print(f"  🔧 OpenAPI spec: {base_url}/openapi.json")
            return True
        else:
            print(f"❌ Documentation endpoints failed")
            print(f"  Docs: {'✅' if docs_ok else '❌'}")
            print(f"  ReDoc: {'✅' if redoc_ok else '❌'}")
            print(f"  OpenAPI: {'✅' if openapi_ok else '❌'}")
            return False
    except Exception as e:
        print(f"❌ Documentation endpoints error: {e}")
        return False

def main():
    """Run all tests."""
    base_url = "http://localhost:8000"
    
    print("🧪 Starting Dual-Language Transcription Service Tests - FastAPI Version")
    print(f"Testing service at: {base_url}")
    print("-" * 70)
    
    # Test health endpoint
    health_ok = test_health_endpoint(base_url)
    print()
    
    # Test models endpoint
    models_ok = test_models_endpoint(base_url)
    print()
    
    # Test documentation endpoints
    docs_ok = test_docs_endpoints(base_url)
    print()
    
    # Create test audio file
    print("Creating test audio file...")
    audio_file = create_test_audio()
    print(f"Created test audio: {audio_file}")
    print()
    
    # Test English transcription
    english_ok = test_english_transcription(base_url, audio_file)
    print()
    
    # Test Khmer transcription
    khmer_ok = test_khmer_transcription(base_url, audio_file)
    print()
    
    # Test legacy endpoint
    legacy_ok = test_legacy_transcription(base_url, audio_file)
    print()
    
    # Cleanup
    try:
        os.unlink(audio_file)
        print("Cleaned up test audio file")
    except:
        pass
    
    # Summary
    print("-" * 70)
    print("📊 Test Summary:")
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Models Endpoint: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"Documentation: {'✅ PASS' if docs_ok else '❌ FAIL'}")
    print(f"English Transcription: {'✅ PASS' if english_ok else '❌ FAIL'}")
    print(f"Khmer Transcription: {'✅ PASS' if khmer_ok else '❌ FAIL'}")
    print(f"Legacy Endpoint: {'✅ PASS' if legacy_ok else '❌ FAIL'}")
    
    passed_tests = sum([health_ok, models_ok, docs_ok, english_ok, khmer_ok, legacy_ok])
    total_tests = 6
    
    if passed_tests == total_tests:
        print(f"\n🎉 All {total_tests} tests passed! FastAPI service is working correctly.")
        print("\n📚 Don't forget to check out the automatic API documentation:")
        print(f"  • Swagger UI: {base_url}/docs")
        print(f"  • ReDoc: {base_url}/redoc")
        return 0
    else:
        print(f"\n⚠️  {passed_tests}/{total_tests} tests passed. Some endpoints may not be available.")
        if english_ok or khmer_ok:
            print("✅ At least one transcription model is working.")
        return 1

if __name__ == "__main__":
    exit(main())
