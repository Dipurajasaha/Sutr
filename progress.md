# Sutr - Development Progress Tracker

## 🤖 Context for AI Assistants (Copilot/Gemini)
This repository is being built strictly according to a microservices architecture plan. 
- **Rule 1:** Each service is fully isolated (no shared databases, no direct internal imports).
- **Rule 2:** Communication is HTTP-only.
- **Rule 3:** The stack is Python 3.11+, FastAPI, Pydantic, and async PostgreSQL.
- **Rule 4:** Work strictly stage-by-stage. Do not jump ahead.

---

## 📍 Current Status
- **Current Stage:** Ready to begin **Stage 3** (Processing Service).
- **Completed Stages:** 1, 2.

---

## ✅ Completed Stages

### Stage 1: Project Initialization & Architecture Setup [COMPLETED]
- **Objective:** Establish the monorepo structure and base configuration.
- **Key Implementations:**
  - Created isolated folder structures for all microservices in `backend/services/`.
  - Set up `docker-compose.yml` with a shared `postgres` container and a `sutr_network`.
  - Created a virtual environment and generated a `base-requirements.txt` containing FastAPI, Uvicorn, SQLAlchemy, AsyncPG, Pydantic, and Pytest.
  - Defined strict API contracts and configs in `backend/libs/common/` (`responses.py`, `config.py`).

### Stage 2: Upload Service [COMPLETED]
- **Objective:** File ingestion and metadata tracking.
- **Location:** `backend/services/upload-service/`
- **Internal Port:** 8001
- **Key Implementations:**
  - **Dependencies:** Added `python-multipart` and `aiofiles`.
  - **Storage:** Files are saved asynchronously to a local `./uploads` directory with UUID-based filenames to prevent collisions.
  - **Database:** Setup async SQLAlchemy (`app.models.file`) tracking `id`, `filename`, `file_type`, `file_path`, and `status`.
  - **Endpoints:**
    - `POST /api/v1/upload/`: Accepts PDF, MP3, WAV, MP4, MKV. Saves file and creates DB record.
    - `GET /api/v1/files/{file_id}`: Retrieves file metadata and status.

---

## ⏳ Pending Stages

### Stage 3: Processing Service (Content Extraction) [UP NEXT]
- **Goal:** Extract text from PDFs (PyMuPDF) and transcribe media (Whisper), then chunk the text for embeddings.

### Stage 4: Vector Service (Embedding & Retrieval)
- **Goal:** Generate embeddings and store them in a local FAISS index for semantic search.

### Stage 5: Chat Service (RAG Pipeline)
- **Goal:** Context-aware Q&A using OpenAI API and retrieved vector chunks.

### Stage 6: Summary Service
- **Goal:** Multi-level document and media summarization using LLMs.

### Stage 7: Media Timestamp Service
- **Goal:** Map relevant RAG chunks back to their original media timestamps for playback.

### Stage 8: API Gateway
- **Goal:** Centralized routing and request aggregation layer.

### Stage 9: Testing & Quality Assurance
- **Goal:** Achieve ≥95% test coverage using pytest.

### Stage 10: Frontend Integration
- **Goal:** Build React/Vue UI for upload, chat, summary, and media playback.

### Stage 11: Deployment & DevOps
- **Goal:** Complete Dockerization and CI/CD pipelines via GitHub Actions.