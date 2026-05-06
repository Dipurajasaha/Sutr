# Sutr - Microservice Project

## Architecture Rules
- **No Shared Database**: Each service manages its own data logic.
- **Isolated Deployments**: Services communicate via HTTP/REST only.
- **Python 3.11+ & FastAPI**: Standardized across all backend services.

## Service Structure
Every service follows this layout:
- `app/api/`: Routing and endpoints
- `app/core/`: Configuration and middleware
- `app/models/`: Database ORM models
- `app/schemas/`: Pydantic validation (API Contracts)
- `app/services/`: Core business logic


## Services Implemented

### 1. Upload Service (Port: 8001)
- **Directory:** `backend/services/upload-service/`
- **Responsibility:** Handles the ingestion of PDF documents, audio (MP3/WAV), and video (MP4/MKV) files.
- **Storage:** 
  - Physical files are stored locally in the `./uploads` directory.
  - File metadata (ID, original name, type, path, status) is tracked via PostgreSQL.
- **Key Endpoints:**
  - `POST /api/v1/upload/`: Uploads a file and returns its tracking metadata.
  - `GET /api/v1/files/{file_id}`: Retrieves the current status and details of an uploaded file.