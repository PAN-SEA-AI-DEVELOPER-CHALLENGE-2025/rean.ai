#!/bin/bash
# Create .env file with Google Speech-to-Text configuration

echo "Creating .env file with your Google STT settings..."

cat > .env << 'EOF'
# Google Cloud Speech-to-Text Configuration
GOOGLE_APPLICATION_CREDENTIALS=/Users/thun/Desktop/pan-sea/voice-scraping-n-segmentation/white-fiber-470711-s7-c73ed6ec8cfe.json
USE_GOOGLE_STT=true
GOOGLE_STT_USE_ENHANCED=true
GOOGLE_STT_MODEL=latest_long

# File and Performance Settings
MAX_FILE_SIZE=104857600
LOG_LEVEL=INFO
TORCH_NUM_THREADS=2
DEBUG=false

# Khmer Language Configuration
KHMER_LANGUAGE_CODE=km-KH
TRANSCRIPTION_SERVICE_URL=

# Google Speech Advanced Settings
GOOGLE_SPEECH_MODEL=latest_long
GOOGLE_SPEECH_USE_ENHANCED=true
GOOGLE_SPEECH_ENABLE_PUNCTUATION=true
GOOGLE_SPEECH_WORD_TIME_OFFSETS=true
GOOGLE_SPEECH_WORD_CONFIDENCE=true
GOOGLE_SPEECH_PROFANITY_FILTER=false

# Voice Processing Configuration  
use_whisperx=true
use_mfa=false
save_audio_chunks=true
cleanup_temp_files=false
EOF

echo "✅ .env file created successfully!"
echo "📁 Location: $(pwd)/.env"
echo ""
echo "🔧 Your settings:"
echo "  - Google STT credentials: white-fiber-470711-s7-c73ed6ec8cfe.json"
echo "  - Enhanced model: latest_long"
echo "  - Word timestamps: enabled"
echo "  - Automatic punctuation: enabled"
echo "  - Khmer language: km-KH"
echo ""
echo "🧪 Test the configuration:"
echo "  python test_enhanced_transcription.py"
