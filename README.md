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

### 4. Chat Service (Port: 8004)
- **Directory:** `backend/services/chat-service/`
- **Responsibility:** Orchestrates a smart, agentic RAG (Retrieval-Augmented Generation) pipeline with conversational memory.
- **Key Features:**
  - **LangChain Agentic Router:** Uses an LLM agent to intelligently decide whether a user's query requires searching the uploaded document or can be answered using context.
  - **Volatile Conversational Memory:** Maintains a rolling window of the last 10 conversation exchanges (20 messages) per session.
  - **Stateless & Secure:** History is stored in-memory and is automatically cleared when the application session ends or the server restarts.
  - **Tool-Calling Integration:** Communicates with the Vector Service via a specialized `search_document` tool to retrieve relevant context only when necessary.
- **Tech Stack:** LangChain, Longcat API (LongCat-Flash-Chat), HTTPX.
- **Key Endpoints:**
  - `POST /api/v1/chat/query/`: Accepts `session_id`, `query`, and `file_id`. Returns the AI's answer along with source chunk references.

### 5. Summary Service (Port: 8005)
- **Directory:** `backend/services/summary-service/`
- **Responsibility:** Aggregates document content and generates multi-level summaries (short and detailed).
- **Key Features:**
  - **Chunk Aggregation:** Efficiently collects and orders all `TextChunk` records associated with a `file_id` to build a comprehensive context for the LLM.
  - **Intelligent Summarization:** Uses the Longcat LLM with specialized prompts to synthesize content into concise paragraphs or detailed bullet points.
  - **Strict Isolation:** Has its own internal `TextChunk` model and database core so the service remains independently runnable without dependencies on other service logic.
- **Tech Stack:** FastAPI, Longcat API (LongCat-Flash-Chat), SQLAlchemy (Async).
- **Key Endpoints:**
  - `POST /api/v1/summary/generate/`: Accepts a `file_id` and a `summary_type` (`short` or `detailed`). Returns the synthesized summary of the document or media file.

### 6. Media Timestamp Service (Port: 8006)
- **Directory:** `backend/services/media-service/`
- **Responsibility:** Maps AI-retrieved text chunks back to their original playable audio/video segments.
- **Key Features:**
    - **Timestamp Mapping:** Retrieves specific `start_time` and `end_time` values for given `chunk_id`s generated during the RAG pipeline.
    - **Segment Calculation:** Formats the extracted data into playable segments to allow frontend UI "Play" buttons to jump to the exact moment a topic is discussed.
    - **Strict Isolation:** Uses an isolated, read-only definition of the database models (`FileMetadata` and `TextChunk`) to fetch required paths and timestamps without breaking service boundaries.
- **Tech Stack:** FastAPI, SQLAlchemy (Async).
- **Key Endpoints:**
    - `GET /api/v1/media/playback/{file_id}`: Accepts a list of `chunk_id`s as query parameters and returns the physical file path along with the playable timestamp segments.

### 7. API Gateway (Port: 8000)
- **Directory:** `backend/services/api-gateway/`
- **Responsibility:** Acts as the centralized entry point and unified interface for the entire Sutr microservice ecosystem.
- **Key Features:**
    - **Reverse Proxy:** Efficiently routes incoming external requests (JSON and multipart file uploads) to the correct internal microservices using asynchronous `httpx` forwarders.
    - **Network Abstraction:** Hides the complexity of internal service ports (8001-8006). The frontend only needs to communicate with `http://localhost:8000/api/`.
    - **CORS Management:** Pre-configured with Cross-Origin Resource Sharing middleware to allow seamless communication with the frontend UI.
- **Tech Stack:** FastAPI, HTTPX, Python-Multipart.
- **Key Endpoints:**
    - `POST /api/upload/`: Routes to Upload Service.
    - `POST /api/process/`: Routes to Processing Service.
    - `POST /api/chat/query/`: Routes to Chat Service.
    - `POST /api/summary/generate/`: Routes to Summary Service.
    - `GET /api/media/playback/{file_id}`: Routes to Media Timestamp Service.
---

  ## 🧪 Testing & Quality Assurance

  Sutr uses an isolated, service-by-service testing approach built on `pytest`, `pytest-asyncio`, and `pytest-cov`. Every microservice is tested independently with a strict coverage gate of **greater than 95%** so failures are localized and coverage regressions are caught early.

  The test suite mocks heavy AI and data-processing dependencies so the tests run quickly and deterministically without requiring network access or GPU hardware. This includes mocked FAISS indexes, Whisper transcription paths, PyMuPDF parsing flows, Longcat API calls, and other external integrations.

  ### Test Infrastructure
  - `scripts/run_tests.sh` runs the full backend test matrix locally, service by service.
  - GitHub Actions CI runs the same service-level checks in isolated environments.
  - Each service spins up its own test database or equivalent isolated test fixture so data never leaks across services.
  - Async endpoint behavior is validated with `pytest-asyncio` and coverage is measured with `pytest-cov`.

  ### Final Coverage Results
  - **Upload Service:** 100%
  - **Processing Service:** 96.49%
  - **Vector Service:** 100%
  - **Chat Service:** 98.00%
  - **Summary Service:** 98.95%
  - **Media Service:** 96.63%
  - **API Gateway:** 100%

  All 7 microservices passed with coverage above the required 95% threshold.

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
