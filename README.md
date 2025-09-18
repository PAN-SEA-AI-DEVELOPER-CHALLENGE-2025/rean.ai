# Pan-Sea Monorepo

Pan-Sea is an education-focused monorepo containing services for audio transcription, Khmer voice scraping/segmentation, and a Next.js frontend for class management and AI-generated summaries.

## Services included

- `pan-sea-backend/` — FastAPI backend for class management, audio processing, embeddings, and LLM-powered summaries.
- `pan-sea-frontend/` — Next.js frontend (TypeScript) for teachers to create/manage classes and view AI summaries.
- `voice-scraping-n-segmentation/` — FastAPI service for extracting and segmenting Khmer audio from YouTube and other sources.
- `whisper-service/` — Flask-based speech-to-text service supporting English (Whisper) and Khmer (MMS) transcription.

## Quick start (development)

Prerequisites: Docker, Docker Compose, Python 3.10+, Node.js 18+ (for frontend development).

1. Clone the repo:

```bash
git clone https://github.com/PAN-SEA-AI-DEVELOPER-CHALLENGE-2025/rean.ai
cd rean.ai
```

2. Run the minimal stack with Docker Compose (recommended):

```bash
docker-compose -f docker-compose.minimal.yml up --build
```

3. To start services individually:

- Backend:
  ```bash
  cd pan-sea-backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

- Frontend:
  ```bash
  cd pan-sea-frontend
  npm install
  npm run dev
  ```

- Voice scraping service:
  ```bash
  cd voice-scraping-n-segmentation
  pip install -r requirements.txt
  python start_server.py --reload
  ```

- Whisper service:
  ```bash
  cd whisper-service
  docker-compose up --build
  ```

## Environment

Each service contains its own `.env.example` or configuration instructions. Check each service README for required environment variables and deployment notes.

## Contributing

- Fork the repo
- Create a feature branch
- Add tests where applicable
- Open a pull request with a clear description of changes

---

This README provides a monorepo-level overview. For detailed instructions and API docs, see each service's `README.md`.
