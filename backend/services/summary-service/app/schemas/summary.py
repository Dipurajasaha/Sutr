from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import Optional

class SummaryType(str, Enum):
    SHORT = "short"
    QUICK = "quick"  # Alias for short
    DETAILED = "detailed"

class SummaryRequest(BaseModel):
    file_id: UUID
    summary_type: SummaryType = SummaryType.SHORT
    store: Optional[bool] = False  # Whether to store in database

class SummaryResponse(BaseModel):
    file_id: UUID
    summary: str
    summary_type: str