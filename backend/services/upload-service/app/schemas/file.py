from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class FileResponse(BaseModel):
    # -- API response contract for file Metadata --
    id: UUID
    filename: str
    file_type: str
    file_path: str
    status: str
    created_at: datetime
    summary_quick: Optional[str] = None
    summary_detailed: Optional[str] = None

    # Modern Pydantic V2 syntax to read SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)