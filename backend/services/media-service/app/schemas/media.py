from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class TimestampSegment(BaseModel):
    # -- start time in seconds --
    start: float
    # -- end time in seconds --
    end: float
    # -- the text associated with this segment --
    text: str

class MediaPlaybackResponse(BaseModel):
    file_id: UUID
    # -- physical path for the frontend to access (via static volume) --
    file_path: str
    # -- list of relevant segments found --
    segments: List[TimestampSegment]