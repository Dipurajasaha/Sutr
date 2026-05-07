from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class SummaryType(str, Enum):
    SHORT = "short"
    DETAILED = "detailed"

class SummaryRequest(BaseModel):
    file_id: UUID
    summary_type: SummaryType = SummaryType.SHORT

class SummaryResponse(BaseModel):
    file_id: UUID
    summary: str
    summary_type: str