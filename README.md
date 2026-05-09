<div align="center">

# ⚡**Sutr**⚡

<img src="https://readme-typing-svg.herokuapp.com?font=Orbitron&weight=900&size=26&duration=2500&pause=1000&color=FFB347&center=true&vCenter=true&width=900&lines=AI-Powered+Document+%26+Multimedia+Q%26A+System;Semantic+Retrieval+%2B+RAG+Architecture;FAISS+%7C+Whisper+%7C+LangChain+%7C+FastAPI" />

</div>

Sutr is a production-ready, fully distributed microservices application designed to process, analyze, and query documents (PDFs) and multimedia (Audio/Video). It enables semantic search, intelligent summarization, and AI-powered Q&A through a Retrieval-Augmented Generation (RAG) pipeline.

---

```mermaid
flowchart LR

A[**Documents**] --> D[**Sutr AI Engine**]
B[**Audio Files**] --> D
C[**Multimedia**] --> D

D --> E[**Semantic Search**]
D --> F[**FAISS Retrieval**]
D --> G[**Whisper Transcription**]
D --> H[**Context-Aware Q&A**]

E --> I[**React Frontend**]
F --> I
G --> I
H --> I
```

---

## 🛠 Core Stack

```yaml
Backend:
  - Python
  - FastAPI
  - Pydantic
  - SQLAlchemy (Async)
  - PostgreSQL
  - asyncpg

AI/ML:
  - sentence-transformers (all-MiniLM-L6-v2)
  - FAISS
  - Whisper (small)
  - LangChain
  - Longcat LLM API

Frontend:
  - React
```

## 🏗️ Microservices Architecture

This project follows a strict microservices architecture to ensure scalability, fault tolerance, and independent deployability.

**Architecture Rules:**
- **Isolated Services:** Each service manages its own database. No shared databases or direct code dependencies.
- **Network Boundaries:** Services communicate exclusively via HTTP/REST using async httpx clients.
- **Independent Lifecycles:** Every service can be deployed, tested, and restarted independently.
- **Standard Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy (Async), PostgreSQL.

**Standard Service Structure:**
```
backend/services/<service-name>/
├── app/
│   ├── api/endpoints.py          # HTTP routes
│   ├── core/                      # Config & database
│   ├── models/                    # SQLAlchemy ORM
│   ├── schemas/                   # Pydantic validation
│   ├── services/                  # Business logic
│   └── main.py                    # FastAPI initialization
├── tests/                         # pytest test suite
└── requirements.txt               # Python dependencies
```

**Dependency Layout:**
- Each microservice can keep its own runtime requirements in `requirements.txt`.
- Test-only packages can live in a separate `requirements-dev.txt` so production images stay smaller.
- Shared packages should only be placed in a common file when multiple services truly need them.
- Docker images should install runtime dependencies only unless the container is meant for test execution.

---

## 🚀 Services Overview

### 1. **Upload Service** (Port: 8001)
- **Responsibility:** File ingestion and metadata management.
- **Supported Formats:** PDF, MP3, WAV, FLAC, M4A (audio), MP4, MKV, AVI, MOV (video).
- **Storage:** Async file persistence with UUID-based tracking in PostgreSQL.
- **Features:** Cascading delete (removes associated vectors when file is deleted).
- **Key Endpoints:**
  - `POST /api/v1/upload/` → Upload and store file metadata.
  - `GET /api/v1/files/` → List all files with summaries.
  - `GET /api/v1/files/{file_id}` → Get file details and status.
  - `PATCH /api/v1/files/{file_id}` → Update filename and summaries.
  - `DELETE /api/v1/files/{file_id}` → Delete file and trigger cascading vector cleanup.

### 2. **Processing Service** (Port: 8002)
- **Responsibility:** Content extraction, chunking, and auto-summarization.
- **PDF Extraction:** PyMuPDF for fast text extraction.
- **Media Transcription:** OpenAI Whisper (small model) for audio/video transcription with native timestamps.
- **Text Chunking:** LangChain RecursiveCharacterTextSplitter (1000 chars, 150 overlap).
- **Auto-Summary:** Generates quick summaries on file completion via Longcat LLM.
- **Text Sanitization:** Removes invalid UTF-8 bytes to prevent database insert failures.
- **Key Endpoints:**
  - `POST /api/v1/process/` → Extract content, chunk, and initiate vector indexing & auto-summary.

### 3. **Vector Service** (Port: 8005)
- **Responsibility:** Semantic embeddings, FAISS indexing, and similarity search.
- **Embedding Model:** sentence-transformers `all-MiniLM-L6-v2` (offline, zero-cost).
- **Vector Store:** Local FAISS index for sub-millisecond similarity search.
- **Database Persistence:** PostgreSQL vector_metadata table for chunk recovery.
- **Features:** Cascading delete removes all vectors for a file.
- **Text Normalization:** Sanitizes chunk text to prevent encoding errors.
- **Key Endpoints:**
  - `POST /api/v1/vectors/index/` → Index text chunks into FAISS + PostgreSQL.
  - `POST /api/v1/vectors/search/` → Semantic search with optional file_id filtering.
  - `GET /api/v1/vectors/files/{file_id}/chunks/` → Fallback chunk retrieval for broad media queries.
  - `DELETE /api/v1/vectors/files/{file_id}/chunks/` → Delete all vectors for a file (cascading).

### 4. **Chat Service** (Port: 8004)
- **Responsibility:** Agentic RAG pipeline with conversational memory.
- **LLM Router:** LangChain agent decides whether to search vectors or respond from context.
- **Memory Model:** Rolling 10-turn (20-message) in-memory conversation history per session.
- **Semantic Context:** Retrieves top-K relevant chunks from vector service on-demand.
- **Vector Tool:** `search_document` tool for intelligent RAG.
- **Session Management:** Stateless; memory cleared on app restart.
- **Key Endpoints:**
  - `POST /api/v1/chat/query/` → Chat with RAG, returns answer + source chunks.
  - `GET /api/v1/chat/history/{session_id}` → Retrieve conversation history.

### 5. **Summary Service** (Port: 8006)
- **Responsibility:** Multi-level document/media summarization.
- **Aggregation:** Collects and orders all chunks for a file_id.
- **LLM Summarization:** Longcat LLM generates concise (short) or detailed summaries.
- **Summary Types:** `short` (bullet points) or `detailed` (structured paragraphs).
- **Database Isolation:** Isolated chunk model; independent from other services.
- **Key Endpoints:**
  - `POST /api/v1/summary/generate` → Generate and store summary for a file.

### 6. **Media Service** (Port: 8007)
- **Responsibility:** Maps AI-retrieved chunks back to playable audio/video segments.
- **Timestamp Mapping:** Extracts start_time and end_time from chunks.
- **Playback Segments:** Formats data for frontend "jump to topic" functionality.
- **Strict Isolation:** Read-only access to file metadata and chunks.
- **Key Endpoints:**
  - `GET /api/v1/media/playback/{file_id}?chunk_ids=...` → Get file path and playable segments.

### 7. **API Gateway** (Port: 8000)
- **Responsibility:** Centralized reverse proxy and request forwarding.
- **Request Types:** JSON, multipart file uploads, streaming responses.
- **CORS:** Pre-configured for frontend access.
- **Proxy Logic:** Async httpx-based forwarding to internal services.
- **Error Handling:** Graceful fallbacks and service availability checks.
- **Key Routes:**
  - `POST /api/upload/` → Upload Service
  - `POST /api/process/` → Processing Service
  - `POST /api/chat/query/` → Chat Service
  - `GET /api/chat/history/{session_id}` → Chat Service
  - `POST /api/vectors/index/` → Vector Service
  - `POST /api/vectors/search/` → Vector Service
  - `DELETE /api/vectors/chunks/{file_id}` → Vector Service (cascading delete)
  - `POST /api/summary/generate` → Summary Service
  - `GET /api/media/playback/{file_id}` → Media Service
  - `GET /api/uploads/{file_path}` → Static file streaming from Upload Service

---
## 🧠 Key Features

### Semantic Search with Context
1. User query is embedded via sentence-transformers
2. FAISS performs sub-ms similarity search
3. Top-K results filtered by optional file_id
4. Vector metadata joins chunk text from PostgreSQL
5. Chat service uses results as context for LLM

---

### Media Q&A with Timestamps
For audio/video files:
1. Whisper transcribes with native timestamps
2. Chunks retain start_time and end_time
3. Chat service retrieves chunks with timestamps
4. Media service maps chunks to playable segments
5. Frontend player jumps to exact moment in video

---

### Auto-Summary on Upload
When a file finishes processing:
1. Processing service marks file as completed
2. Automatically triggers Summary Service
3. Returns quick summary to Upload Service
4. Summary persists in file metadata
5. Frontend displays summary immediately (no extra click)

---

### Cascading Delete
When a user deletes a file:
1. Upload service receives DELETE request
2. Calls vector service to delete all associated vectors
3. Deletes physical file from disk
4. Removes file metadata from database
5. Result: No orphaned records across services

---

### Text Sanitization Pipeline
To prevent invalid UTF-8 errors:
1. Processing service sanitizes transcripts before DB insert
2. Vector service sanitizes chunk text before indexing
3. Removes null bytes and invalid surrogates
4. Encodes/decodes as UTF-8 with error="ignore"
5. Result: Robust handling of noisy media transcription

---

## 📊 Current Database Schema

### PostgreSQL Tables

**files** (Upload Service)
```
id: UUID (PK)
filename: str
file_type: str (document | audio | video)
file_path: str
status: str (pending | processing | completed | failed)
created_at: datetime
summary_quick: TEXT (auto-generated)
summary_detailed: TEXT (optional)
```

**text_chunks** (Processing Service)
```
id: UUID (PK)
file_id: UUID (FK → files.id)
chunk_index: int
text: str
start_time: float (optional, for media)
end_time: float (optional, for media)
```

**vector_metadata** (Vector Service)
```
faiss_id: int (PK, index into FAISS)
chunk_id: UUID (FK → text_chunks.id, unique)
file_id: UUID (FK → files.id, indexed)
text: str (denormalized from chunk for quick access)
start_time: float (optional)
end_time: float (optional)
```

---

## � Docker & Containerization

Sutr is fully containerized with production-ready Docker support, including GPU acceleration for AI workloads.

### Docker Architecture

**Multi-Stage Builds:**
- Optimized Dockerfiles minimize image sizes
- Runtime dependencies only in production images
- Separate `requirements-dev.txt` for test containers

**Container Specifications:**

| Service | Base | Port |
|---------|------|------|
| API Gateway | python:3.11-slim | 8000 |
| Upload Service | python:3.11-slim | 8001 |
| Processing Service | pytorch:2.1-cuda12.1 | 8002 |
| Media Service | python:3.11-slim | 8003 |
| Vector Service | pytorch:2.1-cuda12.1 | 8004 |
| Summary Service | python:3.11-slim | 8005 |
| Chat Service | python:3.11-slim | 8006 |
| PostgreSQL | postgres:15-alpine | 5432 |
| Frontend | node:20-alpine | 5173 |

**GPU Acceleration:**
- Processing Service: GPU-optimized Whisper transcription (~10x faster on NVIDIA hardware)
- Vector Service: GPU-accelerated embeddings via sentence-transformers
- Requires: NVIDIA Docker runtime + compatible GPU (auto-detects, falls back to CPU)

**Networking:**
- All services on private `sutr_network` bridge
- Services communicate via container names (e.g., `http://vector-service:8000`)
- Only API Gateway and Frontend exposed to host via published ports
- No hardcoded `localhost` URLs in production (all dynamic via environment variables)

### Docker Compose Configuration

**Environment Variables (.env):**
```yaml
DATABASE_URL=postgresql+asyncpg://sutr_admin:sutr_password@postgres:5432/sutr_db
UPLOAD_SERVICE_URL=http://upload-service:8000
PROCESS_SERVICE_URL=http://processing-service:8000
VECTOR_SERVICE_URL=http://vector-service:8000
CHAT_SERVICE_URL=http://chat-service:8000
SUMMARY_SERVICE_URL=http://summary-service:8000
MEDIA_SERVICE_URL=http://media-service:8000
LONGCAT_API_KEY=your_key_here
```

**Volumes:**
- `postgres_data` → PostgreSQL persistence
- `uploads` → Shared file storage across services

### Quick Start & Common Commands

```bash
# Start all services
docker compose up -d --build

# View status and logs
docker compose ps
docker compose logs -f                    # All services
docker compose logs -f <service-name>      # Specific service

# Restart and manage
docker compose up -d --build <service-name>  # Rebuild one service
docker compose down -v && docker compose up -d --build  # Clean restart

# Verify services
curl http://localhost:8000/api/files/     # Check API Gateway
docker compose exec processing-service nvidia-smi  # Check GPU
```

### Production Deployment Checklist

- [ ] Update `.env` with production URLs and API keys
- [ ] Change `allow_origins` to specific domain (not `["*"]`)
- [ ] Use external PostgreSQL for data durability
- [ ] Use secrets management (Docker Secrets, AWS Secrets Manager, etc.)
- [ ] Enable logging to centralized system (ELK, CloudWatch, etc.)
- [ ] Configure health checks for orchestration (Kubernetes, ECS)

---

## 🛠️ How to Run Locally (Manual Setup)

If you prefer running services directly without Docker (not recommended - Docker setup above is simpler):

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (running locally)
- Node.js 20+ (for frontend)
- ~4GB RAM

### 1. Start PostgreSQL
```bash
psql -U postgres -c "CREATE DATABASE sutr_db;"
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows
```

### 3. Run Each Service
```bash
cd backend/services/<service-name>
pip install -r requirements.txt
uvicorn app.main:app --reload --port <port>
```

**Service Ports:** Gateway (8000) | Upload (8001) | Processing (8002) | Media (8003) | Vector (8004) | Summary (8005) | Chat (8006)

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

### 5. Verify
```bash
curl http://localhost:8000/api/files/  # Should return: []
```

---

## 🧪 Testing

Each service includes a comprehensive pytest test suite with >95% coverage target.

### Run All Tests
```bash
bash scripts/run_tests.sh
```

### Run Tests for a Single Service
```bash
cd backend/services/<service-name>
pytest -v --cov=app --cov-report=html
```

### Test Infrastructure
- Mocked FAISS indexes (no real indexing needed)
- Mocked Whisper transcription
- Mocked LLM calls (Longcat API)
- Isolated test databases (no data leakage)
- Fast deterministic execution (seconds, not minutes)

---

## 🔄 Service Dependencies

```
Frontend (React)
   ↓
API Gateway (8000)
   ├→ Upload Service (8001)
   ├→ Processing Service (8002)
   │   └→ Vector Service (8005)
   │   └→ Summary Service (8006)
   ├→ Chat Service (8004)
   │   └→ Vector Service (8005)
   ├→ Vector Service (8005)
   ├→ Summary Service (8006)
   ├→ Media Service (8007)
   └→ PostgreSQL (shared across services)
```

---

## 📦 Deployment

Each service is independently deployable as a containerized unit. See `docker-compose.yml` for local dev setup and adapt for production environments (Kubernetes, ECS, etc.).

---
