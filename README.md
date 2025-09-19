# Pan-Sea Monorepo

This repository contains multiple services and tools used for building, transcribing, scraping, and serving speech and RAG (retrieval-augmented generation) features for the Pan-Sea project.

- **Location**: `/Users/thun/Desktop/pan-sea`

## Services

- **pan-sea-backend**
  - Purpose: Core application logic and public APIs for Pan-Sea.
  - What it contains: CRUD classes (e.g., `crud.student`, `crud.class`), summary service, semantic search service, authentication and authorization middleware, request handlers, background tasks, and integrations with vector search and embedding providers.
  - Key responsibilities:
    - Expose REST/HTTP endpoints for the frontend and other services.
    - Implement business logic: student/course management, summarization, document ingestion, and retrieval logic.
    - Provide semantic search using embeddings and vector stores.
    - Orchestrate calls to AI models for summarization and Q&A.

- **pan-sea-frontend**
  - Purpose: User interface for interacting with Pan-Sea features.
  - What it contains: Next.js app, pages/components, Tailwind CSS styling, client-side logic for RAG flows and interactions with the backend.
  - Key responsibilities:
    - Provide responsive UI for users to search, view summaries, and interact with Q&A flows.
    - Handle authentication flows and file uploads where applicable.

- **whisper-service**
  - Purpose: Host and serve the speech model(s) used for transcription.
  - What it contains: FastAPI endpoints to accept audio, run transcription models (locally or via model server), and return transcription results.
  - Key responsibilities:
    - Provide a stable HTTP interface to run transcription.
    - Manage model loading, batching, and resource usage for inference.

- **voice-scraping-n-segmentation**
  - Purpose: Tools collection for scraping audio from sources (e.g., YouTube), segmenting, and cleaning audio using forced-alignment tools.
  - What it contains: Scrapers, segmentation pipelines, VAD (Voice Activity Detection) tuned for Khmer, MFA integration for forced alignment and cleaning, and helper scripts.
  - Key responsibilities:
    - Download and normalize audio from online sources.
    - Apply Intelligent VAD (WebRTC VAD tuned for Khmer tonal characteristics) to split audio into speech segments.
    - Clean and align segments using MFA (Montreal Forced Aligner) and other post-processing tools.

- **speech_dataset**
  - Purpose: Dataset building and merging utilities for training and fine-tuning speech models.
  - What it contains: Dataset builder scripts, merging utilities, metadata, local dataset exports, and scripts for preparing data for training/tuning.
  - Dataset summary:
    1. **Local/Original Dataset**: 81,340 samples (~100+ hours) — broadcast/TTS-quality recordings.
    2. **LSR42 Dataset**: 2,906 samples — male speaker recordings.
    3. **Hugging Face Rinabuoy Dataset**: 26,309 samples (~33+ hours) — community-contributed recordings.
    4. **Combined MEGA Dataset**: 110,555 samples (~138+ hours) — aggregated total used for training/tuning.

## Technology Stack

- pan-sea-backend
  - AI Models & Services:
    - `aisingapore/Llama-SEA-LION-v3-70B-IT` — used for summarization and Q&A flows.
    - Custom Whisper tuning model trained on the Combined MEGA Dataset (~138 hours) — used for transcription.
    - Embeddings: `text-embedding-3-small` (primary), fallback to `text-embedding-004`, and as a last resort `cohere.embed-multilingual-v3`.
    - Vector store: `pgvector` for similarity search.
  - Web framework: FastAPI
  - Database: PostgreSQL

- pan-sea-frontend
  - Framework: Next.js
  - Styling: Tailwind CSS

- whisper-service
  - Web framework: FastAPI
  - Purpose: Serve transcription model(s) via HTTP API

- voice-scraping-n-segmentation
  - Web framework: FastAPI (for any service endpoints)
  - Intelligent VAD: WebRTC VAD (tuned for Khmer characteristics)
  - Text cleaning/segmentation: `whisperx` (dictionary-based enhancements)

## Running the project

Each service has its own `Dockerfile` and `docker-compose.yml` under their respective directories. Refer to each service's README and `DOCKER-README.md` for local development and deployment instructions.

## Contributing

Please follow the repository conventions for branching and pull requests. Run tests in `pan-sea-backend/tests` and ensure any dataset changes are documented in `speech_dataset/`.

## Team

- **Heng Bunkheang — Team Lead**
  - Responsibilities: Lead frontend development, optimize and improve backend performance, coordinate releases and architecture decisions.

- **Duch Panhathun — Backend & ML Engineer**
  - Responsibilities: Implement backend features, manage API and data models, run and maintain machine learning training pipelines.

- **Sokhom Kimheng — Assistant**
  - Responsibilities: Data cleaning, dataset preparation, research support, and assisting other team members as needed.
