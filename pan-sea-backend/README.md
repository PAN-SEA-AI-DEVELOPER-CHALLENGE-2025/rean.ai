<!-- Monorepo note added by script -->
**Note**: This repository is part of the Pan-Sea monorepo. For monorepo-level setup and services overview, see `../README.md`.

# Pan-Sea Backend

A Python FastAPI backend for the Pan-Sea class teaching summarization system using LLM.

## Features

- **Class Management**: Create, manage, and track teaching sessions
- **Real-time Audio Processing**: Live transcription of class sessions
- **LLM-powered Summarization**: Automatic generation of class summaries
- **WebSocket Support**: Real-time communication for live sessions
- **REST API**: Complete CRUD operations for classes and summaries
- **Authentication**: Secure user management for teachers and students
- **File Upload**: Support for audio file processing

## Project Structure

```
pan-sea-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py       # Main API router
│   │       └── endpoints/   # Individual endpoint modules
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication logic
│   │   ├── llm.py           # LLM integration
│   │   └── audio.py         # Audio processing
│   ├── database/            # Database related
│   │   ├── __init__.py
│   │   ├── database.py      # Database connection
│   │   └── models/          # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── class_schemas.py
│   │   └── user_schemas.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── class_service.py
│   │   └── summary_service.py
│   ├── middleware/          # Custom middleware
│   │   ├── __init__.py
│   │   └── logging.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── migrations/              # Database migrations
├── tests/                   # Test files
├── uploads/                 # File upload directory
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. **Clone and navigate to the backend directory**
```bash
cd pan-sea-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your actual values
```

5. **Set up database**
```bash
# Make sure PostgreSQL is running
createdb panseadb
# Run migrations
alembic upgrade head
```

6. **Run the application**
```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

## API Endpoints

### Classes
- `GET /api/v1/classes/` - List all classes
- `POST /api/v1/classes/` - Create a new class
- `GET /api/v1/classes/{id}` - Get class details
- `PUT /api/v1/classes/{id}` - Update class
- `DELETE /api/v1/classes/{id}` - Delete class

### Summaries
- `GET /api/v1/summaries/` - List summaries
- `POST /api/v1/summaries/` - Create summary
- `GET /api/v1/summaries/{id}` - Get summary details

### Real-time
- `WebSocket /ws/class/{class_id}` - Live class session

### Audio
- `POST /api/v1/audio/upload` - Upload audio file with automatic transcription (supports `language` parameter: "english" or "khmer")
- `GET /api/v1/audio/recordings/{class_id}` - Get all audio recordings for a class
- `DELETE /api/v1/audio/recordings/{audio_id}` - Delete audio recording and embeddings
- `GET /api/v1/audio/recordings/{audio_id}/url` - Get presigned URL for audio file
- `POST /api/v1/audio/transcribe/{audio_id}` - Manually transcribe existing audio recording
- `POST /api/v1/audio/test-khmer-embedding` - Test Khmer text embedding capability
- `GET /api/v1/audio/search` - Search audio transcriptions using semantic search

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

### Required Environment Variables

```bash
# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/pan_sea_db"
DATABASE_URL_ASYNC="postgresql+asyncpg://username:password@localhost:5432/pan_sea_db"

# Security
SECRET_KEY="your-super-secret-key-here"

# AWS Bedrock (for embeddings via Cohere Embed Multilingual)
AWS_ACCESS_KEY_ID="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
AWS_REGION="ap-southeast-1"

# OpenAI (Legacy - not used for embeddings)
OPENAI_API_KEY="your-openai-api-key-here"

# External Transcription Service
TRANSCRIPTION_SERVICE_URL="http://13.221.111.151:8000"  # Your Whisper API endpoint
TRANSCRIPTION_SERVICE_TIMEOUT=300  # Timeout in seconds

# AWS S3 Configuration
AWS_ACCESS_KEY_ID="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="your-s3-bucket-name"
```

### Optional Environment Variables

```bash
# Application Settings
DEBUG=false
PORT=8000

# Sea Lion AI (alternative to OpenAI)
SEA_LION_API_KEY="your-sea-lion-api-key"

# Redis
REDIS_URL="redis://localhost:6379"

# CORS
ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

### Audio Transcription Setup

The application now supports both **English** and **Khmer** transcription through an external Whisper API service. The service endpoints are:

- English transcription: `POST {TRANSCRIPTION_SERVICE_URL}/transcribe/english`
- Khmer transcription: `POST {TRANSCRIPTION_SERVICE_URL}/transcribe/khmer`

Configure the `TRANSCRIPTION_SERVICE_URL` in your `.env` file to point to your Whisper API instance.

## Technologies Used

- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **AWS Bedrock + Cohere**: Embeddings via Cohere Embed Multilingual for semantic search
- **OpenAI**: Legacy LLM integration (not used for embeddings)
- **WebSockets**: Real-time communication
- **Redis**: Caching and session management
- **PostgreSQL**: Primary database
- **External Whisper API**: Audio transcription (English & Khmer support)

## Development

Run with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Deployment

### Kubernetes on AWS (EKS)

This project exposes a `/healthz` endpoint suitable for Kubernetes liveness/readiness probes. To deploy on EKS:

1. Build and push the Docker image to Amazon ECR
2. Apply the Kubernetes manifests under `k8s/`
3. Use AWS RDS (Postgres), ElastiCache (Redis), and S3 for storage

See `k8s/README.md` for details and example manifests.

Run tests:
```bash
pytest
```

## License

MIT License
