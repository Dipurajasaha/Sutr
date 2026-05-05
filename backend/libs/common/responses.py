from pydantic import BaseModel
from typing import Any, Optional

class StandardResponse(BaseModel):
    status: str= "success"
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str 
    detail: Optional[Any] = None 