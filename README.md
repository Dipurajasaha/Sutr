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

## 🛠️ How to Run Locally

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Docker Compose
- ~4GB RAM (Whisper model + FAISS index)

### 1. Start Infrastructure
```bash
docker-compose up -d postgres
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\Activate.ps1  # Windows
```

### 3. Run Individual Services
Navigate to each service directory and start with uvicorn:

```bash
cd backend/services/<service-name>
uvicorn app.main:app --reload --port <port>
```

**Service Ports:**
- Upload: 8001
- Processing: 8002
- Chat: 8004
- Vector: 8005
- Summary: 8006
- Media: 8007
- API Gateway: 8000

### 4. Verify All Services are Running
```bash
curl http://localhost:8000/api/files/
```

Should return an empty array `[]` if the database is initialized.

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
