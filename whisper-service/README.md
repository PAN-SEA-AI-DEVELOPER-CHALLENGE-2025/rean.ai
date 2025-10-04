<!-- Monorepo note added by script -->
**Note**: This project is part of the Pan-Sea monorepo. For monorepo-level setup and services overview, see `../README.md`.

# Dual-Language Speech-to-Text Service

A Flask-based web service that provides speech-to-text transcription using:
- **OpenAI Whisper (Turbo)** for English transcription
- **Facebook MMS ASR** for Khmer transcription

Designed for easy deployment on AWS EC2.

> **🆕 Latest Update:** Now supports both English and Khmer with dedicated endpoints using state-of-the-art models!

## Features

- 🌍 **Dual-language support**: English (Whisper) + Khmer (MMS)
- 🎤 State-of-the-art audio transcription models
- 🌐 RESTful API with JSON responses
- 📁 Support for multiple audio formats (WAV, MP3, MP4, FLAC, etc.)
- 🔄 Optional translation to English (Whisper endpoint)
- ⚡ GPU acceleration support
- 🏥 Health check endpoint for load balancers
- 🐳 Docker containerization
- 📊 Detailed transcription with timestamps (English)
- 🔄 Backward compatibility with legacy endpoint

## Supported Audio Formats

- WAV, MP3, MP4, MPEG, MPGA, M4A, WEBM, FLAC, OGG

## API Endpoints

### `POST /transcribe/english`
Transcribe English audio using OpenAI Whisper.

**Parameters:**
- `file` (required): Audio file to transcribe
- `task` (optional): 'transcribe' or 'translate' (default: 'transcribe')

**Example:**
```bash
curl -X POST \
  -F "file=@english_audio.mp3" \
  -F "task=transcribe" \
  http://localhost:5000/transcribe/english
```

**Response:**
```json
{
  "text": "Hello, this is a test transcription.",
  "language": "en",
  "model": "whisper",
  "task": "transcribe",
  "filename": "english_audio.mp3",
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Hello, this is a test transcription."
    }
  ]
}
```

### `POST /transcribe/khmer`
Transcribe Khmer audio using Facebook MMS ASR.

**Parameters:**
- `file` (required): Audio file to transcribe

**Example:**
```bash
curl -X POST \
  -F "file=@khmer_audio.mp3" \
  http://localhost:5000/transcribe/khmer
```

**Response:**
```json
{
  "text": "សួស្តី នេះជាការសាកល្បងការចម្លង។",
  "language": "khm",
  "model": "mms",
  "task": "transcribe",
  "filename": "khmer_audio.mp3"
}
```

### `POST /transcribe` (Legacy)
Legacy endpoint that defaults to English transcription for backward compatibility.

### `GET /health`
Health check endpoint.

### `GET /models`
List available models and their status.

### `GET /`
Service information and API documentation.

## Quick Start

### Using Docker (Recommended)

1. **Clone and build:**
   ```bash
   git clone <your-repo>
   cd whisper-service
   docker-compose up --build
   ```

2. **Test the service:**
   ```bash
   curl http://localhost:5000/health
   ```

3. **Test both endpoints:**
   ```bash
   # Test English transcription
   curl -X POST -F "file=@english_audio.mp3" http://localhost:5000/transcribe/english
   
   # Test Khmer transcription  
   curl -X POST -F "file=@khmer_audio.mp3" http://localhost:5000/transcribe/khmer
   ```

### Using Python directly

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the service:**
   ```bash
   python app.py
   ```

## AWS EC2 Deployment

### Option 1: Automated Setup Script

1. **Copy files to EC2:**
   ```bash
   scp -i your-key.pem -r . ubuntu@your-ec2-ip:~/whisper-service/
   ```

2. **SSH into EC2 and run setup:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   cd whisper-service
   chmod +x startup.sh
   ./startup.sh
   ```

### Option 2: Manual Docker Deployment

1. **Install Docker on EC2:**
   ```bash
   sudo apt-get update
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Build and run:**
   ```bash
   docker build -t whisper-service .
   docker run -d -p 80:5000 --name whisper-service whisper-service
   ```

### Option 3: Using Docker Compose

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

- `WHISPER_MODEL_SIZE`: Whisper model size (tiny, base, small, medium, large, large-v2, large-v3, turbo) - default: turbo
- `HOST`: Server host - default: 0.0.0.0
- `PORT`: Server port - default: 5000

### Supported Models

**English (Whisper):**
- All OpenAI Whisper models: tiny, base, small, medium, large, large-v2, large-v3, turbo

**Khmer (MMS):**
- Facebook MMS-1B-All model with Khmer language adapter

### Model Sizes and Performance

| Model    | Parameters | VRAM    | Speed      | Accuracy | Notes                    |
|----------|------------|---------|------------|----------|--------------------------|
| tiny     | 39 M       | ~1 GB   | Fastest    | Basic    | Good for testing         |
| base     | 74 M       | ~1 GB   | Fast       | Good     | Balanced option          |
| small    | 244 M      | ~2 GB   | Medium     | Better   | Good accuracy/speed      |
| medium   | 769 M      | ~5 GB   | Slow       | Great    | Production quality       |
| large    | 1550 M     | ~10 GB  | Slower     | Best     | Original large model     |
| large-v2 | 1550 M     | ~10 GB  | Slower     | Best     | Improved large model     |
| large-v3 | 1550 M     | ~10 GB  | Slower     | Best     | Latest large model       |
| turbo    | 809 M      | ~6 GB   | Very Fast  | Excellent| **Recommended**: Fast + accurate |

**🚀 New:** The `turbo` model (Sept 2024) offers the best balance of speed and accuracy!

## AWS EC2 Instance Recommendations

### For Production Use:
- **Instance Type:** t3.large or larger (CPU-based) or g4dn.xlarge (GPU-based)
- **Storage:** 30GB+ EBS volume (both models require more space)
- **Memory:** 8GB+ RAM (16GB+ recommended for optimal performance)
- **Security Group:** Allow inbound traffic on port 80 and/or 5000

### For Development/Testing:
- **Instance Type:** t3.medium  
- **Model Size:** base (Whisper)
- **Storage:** 20GB EBS volume

**Note:** Khmer transcription requires downloading the MMS model (~2.5GB), so ensure adequate storage and initial startup time.

## Security Considerations

- The service runs as a non-root user in the container
- File size is limited to 100MB by default
- Only specified audio formats are accepted
- Temporary files are automatically cleaned up
- Consider using HTTPS in production (add nginx/ALB)

## Monitoring

### Health Check
```bash
curl http://your-ec2-ip/health
```

### Container Logs
```bash
docker logs whisper-service-container
```

### Performance Monitoring
```bash
# Check resource usage
docker stats whisper-service-container

# Check GPU usage (if available)
nvidia-smi
```

## Troubleshooting

### Common Issues

1. **Out of Memory:**
   - Use a smaller model (tiny or base)
   - Increase EC2 instance memory
   - Limit concurrent requests

2. **Slow Transcription:**
   - Use GPU-enabled EC2 instance (g4dn family)
   - Use smaller model for faster processing
   - Optimize audio file size/format

3. **Service Not Starting:**
   - Check Docker logs: `docker logs whisper-service-container`
   - Verify all dependencies are installed
   - Ensure sufficient disk space for model download

### Log Files
- Application logs are available via `docker logs`
- For persistent logging, mount a volume to `/app/logs`

## API Usage Examples

### Python Examples

**English Transcription:**
```python
import requests

url = "http://your-ec2-ip:5000/transcribe/english"
files = {"file": open("english_audio.mp3", "rb")}
data = {"task": "transcribe"}

response = requests.post(url, files=files, data=data)
result = response.json()
print(f"English: {result['text']}")
```

**Khmer Transcription:**
```python
import requests

url = "http://your-ec2-ip:5000/transcribe/khmer"
files = {"file": open("khmer_audio.mp3", "rb")}

response = requests.post(url, files=files)
result = response.json()
print(f"Khmer: {result['text']}")
```

### cURL Examples
```bash
# English transcription
curl -X POST -F "file=@english_audio.mp3" http://localhost:5000/transcribe/english

# English with translation to English
curl -X POST -F "file=@spanish_audio.mp3" -F "task=translate" http://localhost:5000/transcribe/english

# Khmer transcription
curl -X POST -F "file=@khmer_audio.mp3" http://localhost:5000/transcribe/khmer

# Legacy endpoint (defaults to English)
curl -X POST -F "file=@audio.mp3" http://localhost:5000/transcribe
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review container logs
3. Open an issue on GitHub
