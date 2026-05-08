from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary_manager import generate_summary

router = APIRouter()

@router.post("/generate", response_model=SummaryResponse)
async def request_summary(request: SummaryRequest, db: AsyncSession = Depends(get_db)):
    # -- trigger the summarization logic --
    summary_text = await generate_summary(db, str(request.file_id), request.summary_type)
    
    return SummaryResponse(
        file_id=request.file_id,
        summary=summary_text,
        summary_type=request.summary_type
    )