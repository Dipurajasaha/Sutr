import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from openai import AsyncOpenAI

from app.core.config import settings 
from app.models.chunk import TextChunk


# -- initialize the longcat client --
client = AsyncOpenAI(
    api_key=settings.LONGCAT_API_KEY,
    base_url=settings.LONGCAT_BASE_URL
)


##########################################################################################
# -- fetches all chunks for a file, combines them, and generates a summary --
##########################################################################################
async def generate_summary(db: AsyncSession, file_id: str, summary_type: str) -> str:
    # -- 1. Convert file_id string to UUID object for database query --
    try:
        file_uuid = uuid.UUID(file_id) if isinstance(file_id, str) else file_id
    except (ValueError, AttributeError):
        return "Invalid file_id format."
    
    # -- 2. fetch all text chunks for the given file_id --
    result = await db.execute(
        select(TextChunk.text).where(TextChunk.file_id == file_uuid).order_by(TextChunk.chunk_index)
    )    
    chunks = result.scalars().all()

    if not chunks:
        return "No content found to summarize."
    
    # -- 3. aggregate text chunks --
    full_text = " ".join(chunks)

    # -- 4. define prompt based on summary type --
    prompt_instruction = (
        "Provide a concise 3-5 sentence summary." if summary_type == "short" 
        else "Provide a detailed summary with bullet points covering all key topics."
    )

    # -- 5. call longcat LLM --
    try:
        response = await client.chat.completions.create(
            model=settings.LONGCAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional document summarizer."},
                {"role": "user", "content": f"{prompt_instruction}\n\nContent:\n{full_text[:12000]}"} # -- simple truncation for context limits --
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Summarization failed: {str(e)}"
