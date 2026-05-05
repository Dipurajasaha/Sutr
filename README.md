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