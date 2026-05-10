# Sutr Project Architecture

```mermaid
flowchart TB
    %% Client layer
    U[User] --> F[frontend]

    %% API gateway and orchestration
    F --> AG[api-gateway]
    AG --> CS[chat-service]
    AG --> MS[media-service]
    AG --> PS[processing-service]
    AG --> SS[summary-service]
    AG --> US[upload-service]
    AG --> VS[vector-service]

    %% Chat pipeline
    CS --> VS
    CS --> SS
    CS --> AG

    %% Media and processing pipeline
    MS --> PS
    PS --> VS
    PS --> US

    %% Upload pipeline
    US --> PS
    US --> VS
    US --> MS

    %% Summary pipeline
    SS --> VS

    %% Shared backend libraries
    AG -.-> CL[backend/libs/common]
    CS -.-> CL
    MS -.-> CL
    PS -.-> CL
    SS -.-> CL
    US -.-> CL
    VS -.-> CL

    %% Persistent storage and external services
    US --> UF[(uploads/)]
    CS --> CH[(chat_history.json)]
    VS --> FS[(faiss_store/)]
    PS --> DB[(backend processing artifacts)]
    MS --> MD[(media files / previews)]

    CS --> EXT1[LLM / RAG providers]
    PS --> EXT2[Transcription / media parsing]
    VS --> EXT3[Vector search index]

    %% Deployment layer
    DC[docker-compose.yml] -. orchestrates .-> AG
    DC -. orchestrates .-> CS
    DC -. orchestrates .-> MS
    DC -. orchestrates .-> PS
    DC -. orchestrates .-> SS
    DC -. orchestrates .-> US
    DC -. orchestrates .-> VS

    classDef frontend fill:#1f2937,stroke:#60a5fa,color:#fff,stroke-width:2px;
    classDef service fill:#111827,stroke:#a78bfa,color:#fff,stroke-width:1.5px;
    classDef storage fill:#0f172a,stroke:#34d399,color:#fff,stroke-width:1.5px;
    classDef external fill:#3f3f46,stroke:#f59e0b,color:#fff,stroke-width:1.5px;
    classDef deploy fill:#27272a,stroke:#f472b6,color:#fff,stroke-width:1.5px;

    class F frontend;
    class AG,CS,MS,PS,SS,US,VS,CL service;
    class UF,CH,FS,DB,MD storage;
    class EXT1,EXT2,EXT3 external;
    class DC deploy;
```

## Notes

- `frontend` is shown as a single client block, per request.
- `api-gateway` routes requests to the domain services.
- `chat-service` coordinates retrieval and response generation through the vector store and summary layer.
- `upload-service` handles file ingress and hands work off to processing and media flows.
- `processing-service` prepares content for downstream retrieval and analysis.
- `vector-service` owns similarity search and FAISS-backed indexing.
- `summary-service` produces condensed outputs for document summaries.
- `media-service` manages media-oriented access and playback related operations.
- `backend/libs/common` contains shared configuration and response helpers used across services.
- `docker-compose.yml` orchestrates the full local stack.
