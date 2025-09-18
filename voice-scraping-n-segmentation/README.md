# Khmer Voice Scraping & Segmentation API 🇰🇭

A comprehensive FastAPI-based service specialized for Khmer voice processing, scraping, and segmentation with advanced ML capabilities. Designed specifically for processing Khmer language audio content and preparing training data for Khmer speech recognition models.

## 🏗️ Project Structure

```
voice-scraping-n-segmentation/
├── service/                    # Business logic layer
│   ├── __init__.py
│   └── youtube_extractor.py   # Core audio extraction service
├── router/                     # API endpoints layer
│   ├── __init__.py
│   ├── audio_router.py        # FastAPI routes
│   └── models.py              # Pydantic data models
├── config/                     # Configuration management
│   ├── __init__.py
│   └── settings.py            # App configuration
├── data/                       # Temporary data storage
│   └── temp/                  # Temporary downloads
├── result/                     # Extracted audio files
├── examples/                   # Usage examples
│   └── api_client.py          # API client examples
├── main.py                     # FastAPI application
├── start_server.py            # Server startup script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Khmer Language Features

### Core Audio Processing
- **🎵 YouTube Audio Extraction**: Download and convert YouTube videos to WAV format
- **☁️ AWS S3 Integration**: Automatic upload to your S3 bucket with Khmer metadata
- **🔄 Multiple Sample Rates**: Support for 16kHz, 22kHz, 44kHz, 48kHz
- **✂️ Time Segment Extraction**: Extract specific time ranges from videos
- **📦 Batch Processing**: Process multiple Khmer videos simultaneously

### Khmer Voice Processing Pipeline
- **🎙️ WebRTC VAD**: Voice Activity Detection optimized for Khmer speech patterns
- **🗣️ Whisper Transcription**: High-quality Khmer speech-to-text (language code: 'km')
- **🔤 Montreal Forced Alignment**: Word-level timestamp refinement (requires custom Khmer models)
- **📊 CSV Metadata Export**: UTF-8 encoded data with Khmer text, transcriptions, and speaker info
- **🎯 Speaker Detection**: Basic speaker identification for Khmer speakers
- **⚡ Async Processing**: Background processing for long Khmer audio files

### Khmer-Specific Optimizations
- **🇰🇭 Language Support**: Native Khmer Unicode handling
- **⏱️ Optimized Chunking**: 1.5-5 second chunks suitable for Khmer sentence structure
- **🔊 VAD Tuning**: Less aggressive voice detection for tonal language characteristics
- **📝 Text Encoding**: UTF-8 support for proper Khmer script display
- **🔍 URL Validation**: Validate YouTube URLs before processing
- **🗂️ S3 File Management**: List, delete, and manage files in S3
- **🔐 Presigned URLs**: Generate secure access URLs for S3 objects

## 📋 Requirements

- **Python 3.8+**
- **FFmpeg** (for audio processing)
- **Internet connection** (for YouTube access)

## 🛠️ Installation

### 1. Install System Dependencies

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to PATH

### 2. Install Python Dependencies

```bash
# Clone or download the project
cd voice-scraping-n-segmentation

# Install Python packages
pip install -r requirements.txt
```

### 3. Quick Start

```bash
# Start the API server
python start_server.py

# Or with auto-reload for development
python start_server.py --reload

# Or install dependencies automatically
python start_server.py --install-deps
```

The API will be available at:
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with your configuration:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Audio settings
SAMPLE_RATE=22050
AUDIO_FORMAT=wav
MAX_DURATION=3600

# Processing settings
MAX_CONCURRENT_DOWNLOADS=3
TIMEOUT=300

# AWS S3 Configuration (for cloud storage)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=pansea-storage
AWS_S3_USE_SSL=true
AWS_S3_VERIFY_SSL=true

# S3 Automation (optional)
S3_AUTO_UPLOAD=false
S3_DELETE_LOCAL_AFTER_UPLOAD=false
S3_PREFIX==

# Transcription Service (optional)
TRANSCRIPTION_SERVICE_URL=http://your-transcription-service:8000
TRANSCRIPTION_SERVICE_TIMEOUT=300
```

### Using Your Existing S3 Configuration

Based on your provided `.env`, the service will automatically connect to:
- **Bucket**: `pansea-storage` 
- **Region**: `ap-southeast-1`
- **AWS Credentials**: Using your provided access keys

## 📖 API Usage

### Using the API Client

```python
from examples.api_client import AudioExtractionClient

# Initialize client
client = AudioExtractionClient("http://localhost:8000")

# Extract audio with S3 upload
result = client.extract_audio(
    youtube_url="https://www.youtube.com/watch?v=VIDEO_ID",
    filename="my_audio",
    sample_rate=16000,
    start_time=60,        # Start at 1 minute
    duration=30,          # Extract 30 seconds
    upload_to_s3=True     # Upload to S3
)

print(f"Extracted: {result['data']['filename']}")
if result['data']['s3_uploaded']:
    print(f"S3 URL: {result['data']['s3_url']}")

# List files in S3
s3_files = client.list_s3_files()
print(f"S3 files: {s3_files['total_count']}")
```

### Direct HTTP Requests

**Get Video Info:**
```bash
curl -X POST "http://localhost:8000/api/audio/info" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

**Extract Audio with S3 Upload:**
```bash
curl -X POST "http://localhost:8000/api/audio/extract" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://www.youtube.com/watch?v=VIDEO_ID",
       "filename": "speech_sample",
       "sample_rate": 16000,
       "start_time": 0,
       "duration": 30,
       "upload_to_s3": true
     }'
```

**List S3 Files:**
```bash
curl "http://localhost:8000/api/audio/s3/files"
```

**Get S3 Status:**
```bash
curl "http://localhost:8000/api/audio/s3/status"
```

**Download File:**
```bash
curl -O "http://localhost:8000/api/audio/download/speech_sample.wav"
```

## 🧪 Testing Voice Processing Pipeline

### Quick Testing Methods

#### 1. Automated Test Suite
```bash
python tests/test_voice_processing.py
```

#### 2. Interactive Demo
```bash
python examples/test_khmer_voice_processing.py
```

#### 3. Command Line Testing
```bash
./test_voice_api.sh
# or with custom file
./test_voice_api.sh path/to/your/khmer_audio.wav
```

### Voice Processing API Examples

**Process Khmer Audio File:**
```bash
curl -X POST "http://localhost:8000/api/voice/process" \
     -H "Content-Type: application/json" \
     -d '{
       "local_file_path": "data/temp/khmer_audio.wav",
       "use_mfa": false,
       "save_chunks": true,
       "vad_aggressiveness": 2,
       "min_chunk_duration": 1.5,
       "max_chunk_duration": 5.0,
       "transcription_model": "base"
     }'
```

**Get Session Results:**
```bash
curl "http://localhost:8000/api/voice/sessions/{session_id}"
```

**Download CSV Metadata:**
```bash
curl -O "http://localhost:8000/api/voice/download/chunks.csv"
curl -O "http://localhost:8000/api/voice/download/words.csv"
```

### Expected Results

The voice processing pipeline will:
1. 🎙️ **Split audio** into 1.5-5 second chunks using WebRTC VAD
2. 🗣️ **Transcribe** each chunk to Khmer text using Whisper
3. 🔤 **Align** word-level timestamps (if MFA enabled)
4. 📊 **Export** metadata to CSV files:
   - `chunks.csv`: Chunk-level data with transcriptions
   - `words.csv`: Word-level timestamps and confidence
5. 💾 **Save** individual chunk audio files (if enabled)

For detailed testing instructions, see [TESTING_GUIDE.md](TESTING_GUIDE.md).

## 🎵 Sample Rate Guide

Choose the appropriate sample rate for your use case:

| Sample Rate | Use Case | Description |
|-------------|----------|-------------|
| **16kHz** | Speech Recognition | Optimal for ASR models, voice assistants |
| **22.05kHz** | General Audio | Balanced quality/size for most ML tasks |
| **44.1kHz** | Music/High Quality | CD quality for music analysis |
| **48kHz** | Professional | Broadcasting and professional audio |

## 📚 API Endpoints

### Core Audio Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | API documentation |
| POST | `/api/audio/info` | Get video information |
| POST | `/api/audio/extract` | Extract audio (sync) |
| POST | `/api/audio/extract-async` | Extract audio (async) |
| POST | `/api/audio/extract-batch` | Batch extraction |
| POST | `/api/audio/validate` | Validate YouTube URL |
| GET | `/api/audio/files` | List local files |
| GET | `/api/audio/download/{filename}` | Download local file |
| GET | `/api/audio/config` | Get configuration |
| POST | `/api/audio/cleanup` | Clean temp files |

### S3 Storage Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audio/s3/status` | S3 service status |
| GET | `/api/audio/s3/files` | List S3 files |
| POST | `/api/audio/s3/upload` | Upload file to S3 |
| DELETE | `/api/audio/s3/{key}` | Delete S3 file |
| GET | `/api/audio/s3/{key}/info` | Get S3 file info |
| POST | `/api/audio/s3/presigned-url` | Generate presigned URL |

## 🔄 Development

**Start with auto-reload:**
```bash
python start_server.py --reload
```

**Run with custom settings:**
```bash
python start_server.py --host 127.0.0.1 --port 8000 --workers 4
```

**Test the API:**
```bash
python examples/api_client.py
```

## 📁 Output Files

Extracted audio files are saved in the `result/` directory with the following format:
- **Format**: WAV (uncompressed)
- **Channels**: Mono (single channel)
- **Bit depth**: 32-bit float
- **Naming**: `{video_title}_{sample_rate}hz.wav`

Example output:
```
result/
├── My_Video_Title_16000hz.wav
├── Speech_Sample_22050hz_60s_30s.wav
└── batch_audio_001.wav
```

## 🚨 Error Handling

The API provides detailed error responses:

```json
{
  "error": "Invalid YouTube URL",
  "detail": "The provided URL is not a valid YouTube video"
}
```

Common error scenarios:
- Invalid YouTube URLs
- Network connectivity issues
- FFmpeg not installed
- Insufficient disk space
- Video not available/private

## 🔒 Legal Notice

⚠️ **Important**: Always respect copyright laws and YouTube's Terms of Service. Only download content you have permission to use. This tool is intended for educational and research purposes with appropriately licensed content.

## 🛠️ Troubleshooting

**FFmpeg not found:**
```bash
# Check if FFmpeg is installed
ffmpeg -version

# Install if missing (macOS)
brew install ffmpeg
```

**Dependencies issues:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Port already in use:**
```bash
# Use different port
python start_server.py --port 8000
```

**Memory issues with long videos:**
- Use `start_time` and `duration` parameters
- Process videos in smaller segments
- Increase system RAM

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect copyright laws and platform terms of service.

---

**Happy audio extraction! 🎵**