# Sutr - AI-Powered Document & Multimedia Q&A System

Sutr is a highly scalable, full-stack AI application designed to process, analyze, and query documents (PDFs) and multimedia (Audio/Video). It allows users to upload files, generate intelligent summaries, perform semantic searches, and interact with an AI chatbot grounded in the uploaded content via a Retrieval-Augmented Generation (RAG) pipeline.

## 🏗️ Microservices Architecture Rules
This project is strictly built on a distributed microservices architecture to ensure scalability, fault tolerance, and independent deployability.
- **Strict Isolation**: Each service manages its own data logic. **No shared databases**.
- **Network Boundaries**: Services communicate via HTTP/REST only. **No direct internal code imports** between services.
- **Independent Lifecycles**: Every service can be booted, tested, and deployed independently.
- **Tech Stack Standardization**: Python 3.11+, FastAPI, Pydantic, and Async PostgreSQL are standard across all backend services.

## 📂 Standard Service Structure
Every microservice in the `backend/services/` directory strictly follows this Domain-Driven Design (DDD) layout:
- `app/api/`: Routing and HTTP endpoints.
- `app/core/`: Configuration, middleware, and database session management.
- `app/models/`: SQLAlchemy ORM models (Database schema).
- `app/schemas/`: Pydantic validation models (API Contracts).
- `app/services/`: Core business logic and AI processing.

---

## 🚀 Services Implemented (Current State)

### 1. Upload Service (Port: 8001)
- **Directory:** `backend/services/upload-service/`
- **Responsibility:** Handles the ingestion of PDF documents, audio (MP3/WAV), and video (MP4/MKV) files.
- **Storage:** Physical files are stored asynchronously in a local `./uploads` volume. File metadata is tracked via PostgreSQL.
- **Key Endpoints:**
  - `POST /api/v1/upload/`: Ingests a file and returns its UUID-based tracking metadata.
  - `GET /api/v1/files/{file_id}`: Retrieves the current status and details of an uploaded file.

### 2. Processing Service (Port: 8002)
- **Directory:** `backend/services/processing-service/`
- **Responsibility:** Extracts text from files and chunks it for embedding.
- **Engines:** 
  - **PDFs:** `PyMuPDF` for fast text extraction.
  - **Media:** Local `Whisper (small)` model for audio/video transcription with native timestamp extraction.
  - **Chunking:** `langchain-text-splitters` (1000 chars, 150 overlap).
- **Key Endpoints:**
  - `POST /api/v1/process/`: Triggers extraction, creates text chunks, and persists them to PostgreSQL.

### 3. Vector Service (Port: 8003)
- **Directory:** `backend/services/vector-service/`
- **Responsibility:** Generates AI embeddings from text chunks and performs high-speed semantic searches.
- **Engines:**
  - **Embeddings:** Local `sentence-transformers` (`all-MiniLM-L6-v2`) for offline, zero-cost vectorization.
  - **Vector Store:** Local `FAISS` index for fast similarity search.
- **Key Endpoints:**
  - `POST /api/v1/vectors/index/`: Converts text chunks to vectors and stores them in FAISS and PostgreSQL.
  - `POST /api/v1/vectors/search/`: Takes a user query, embeds it, and retrieves the Top-K most relevant document/media chunks.

---

## 🛠️ How to Run Locally

**1. Start the Base Infrastructure (Database)**
```bash
docker-compose up -d postgres
```

**2. Run Individual Services**

Navigate to the respective service directory and run:

```bash
source venv/bin/activate
cd backend/services/<service-name>
uvicorn app.main:app --reload --port <service-port>
```

Check the Services Implemented section above for the correct port numbers.

---
