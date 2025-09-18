#!/usr/bin/env python3
"""
Google Cloud Speech-to-Text Setup Helper

This script helps you set up Google Cloud credentials for accurate word timestamps.
"""

import os
import json
import subprocess
from pathlib import Path

def check_gcloud_cli():
    """Check if Google Cloud CLI is installed"""
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Google Cloud CLI not found")
    print("📥 Install it from: https://cloud.google.com/sdk/docs/install")
    return False

def check_existing_credentials():
    """Check for existing credentials"""
    creds_env = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_env and os.path.exists(creds_env):
        print(f"✅ Found credentials: {creds_env}")
        return creds_env
    
    # Check common locations
    common_paths = [
        "/Users/thun/Desktop/pan-sea/whisper-service/gcloud-key.json",
        "/Users/thun/.config/gcloud/application_default_credentials.json",
        "./gcloud-key.json",
        "./credentials.json"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ Found potential credentials: {path}")
            return path
    
    print("❌ No credentials found")
    return None

def test_credentials(creds_path):
    """Test if credentials work"""
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        from google.cloud import speech
        client = speech.SpeechClient()
        print("✅ Credentials are valid!")
        return True
    except Exception as e:
        print(f"❌ Credentials test failed: {e}")
        return False

def create_test_config():
    """Create a test configuration for Google STT"""
    return {
        'use_google_stt': True,
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        'GOOGLE_STT_USE_ENHANCED': True,
        'GOOGLE_STT_MODEL': 'latest_long',
        'TRANSCRIPTION_SERVICE_URL': ''  # Force Google STT
    }

def main():
    print("🔧 Google Cloud Speech-to-Text Setup Helper")
    print("=" * 50)
    
    # Step 1: Check CLI
    print("\n1️⃣ Checking Google Cloud CLI...")
    has_cli = check_gcloud_cli()
    
    # Step 2: Check credentials
    print("\n2️⃣ Checking for credentials...")
    creds_path = check_existing_credentials()
    
    if not creds_path:
        print("\n📋 To set up credentials:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create/select a project")
        print("3. Enable Speech-to-Text API")
        print("4. Go to IAM & Admin → Service Accounts")
        print("5. Create service account with 'Cloud Speech Client' role")
        print("6. Download JSON key file")
        print("7. Save it as: /Users/thun/Desktop/pan-sea/whisper-service/gcloud-key.json")
        print("8. Run this script again")
        return
    
    # Step 3: Test credentials
    print(f"\n3️⃣ Testing credentials: {creds_path}")
    if test_credentials(creds_path):
        # Step 4: Create .env file
        print("\n4️⃣ Creating .env configuration...")
        env_path = "/Users/thun/Desktop/pan-sea/voice-scraping-n-segmentation/.env"
        
        env_content = f"""# Google Speech-to-Text Configuration
GOOGLE_APPLICATION_CREDENTIALS={creds_path}
USE_GOOGLE_STT=true
GOOGLE_STT_USE_ENHANCED=true
GOOGLE_STT_MODEL=latest_long
TRANSCRIPTION_SERVICE_URL=

# Voice Processing Configuration  
use_whisperx=true
use_mfa=false
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created {env_path}")
        print("\n🎯 Setup complete! Now run:")
        print("  python test_enhanced_transcription.py")
    else:
        print("\n❌ Credentials are not working. Please check the JSON file.")

if __name__ == "__main__":
    main()
