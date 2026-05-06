from pydantic import BaseModel
from uuid import UUID

# -- schema for incoming file processing requests --
class ProcessRequest(BaseModel):
    file_id: UUID
    file_path: str      # the physical path to the file
    file_type: str      # 'document', 'audio', 'video'

# -- schema for the processing completion response --
class ProcessResponse(BaseModel):
    status: str
    file_id: str
    total_chunks: int
    message: str