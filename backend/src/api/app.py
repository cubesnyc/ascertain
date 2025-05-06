import asyncio
from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, FastAPI, HTTPException

from src.ai.client import OpenAIError
from src.db.engine import init_db
from src.services.schema import DocumentCreate
from src.services import documents as documents_service
from src.services import ai as ai_service
from src.api.schema import DocumentGetResponse, DocumentPostResponse, ExtractStructuredRequest, ExtractStructuredResponse, HealthCheckResponse, DocumentPostRequest, QuestionPostRequest, QuestionPostResponse, SummarizePostResponse, SummarizePostRequest, ToFHIRRequest, ToFHIRResponse
from src._logging import get_logger

logger = get_logger(__name__)

init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):    
    chunking_worker = asyncio.create_task(ai_service.document_chunking_worker())

    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint to verify if the API is running.
    """

    return HealthCheckResponse(status="OK")

@app.get("/documents", response_model=DocumentGetResponse)
async def get_documents():
    """
    Get all documents from the database.
    """
    return DocumentGetResponse(documents = documents_service.get_documents())

@app.post("/documents", response_model=DocumentPostResponse, status_code = 202)
async def post_documents(req: DocumentPostRequest, background: BackgroundTasks ):
    """
    Insert a document into the database.
    """
    documents_service.create_document(DocumentCreate(title =req.title, content = req.content))

    return DocumentPostResponse()

@app.post("/answer_question", response_model=QuestionPostResponse)
async def post_answer_question(req: QuestionPostRequest):
    """
    Answer a question based on the document content.
    """
    logger.debug(f"{req}")

    answer = await ai_service.get_question_answer(req.question)
    return QuestionPostResponse(**answer.model_dump())

@app.post("/summarize_note", response_model=SummarizePostResponse)
async def post_summarize_note(req: SummarizePostRequest):
    """
    Summarize a medical document.
    """

    try:
        logger.debug(f"{req}")

        summary = await ai_service.summarize_text(req.content)
        return SummarizePostResponse(summary = summary)
    
    except OpenAIError as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="OpenAI API error")
    
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/extract_structured", response_model=ExtractStructuredResponse)
async def post_extract_structured(req: ExtractStructuredRequest):
    """
    Process raw text and return a structured JSON object with specific fields extracted and enriched with relevant codes.
    """
    try:
        logger.debug(f"received: {req}")

        r = await ai_service.get_structured_note_agentic(req.raw_note)
        return r

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    
@app.post("/to_fhir", response_model=ToFHIRResponse, response_model_exclude_none=True)
async def post_to_fhir(req: ToFHIRRequest):
    """
    Convert the note returned from /extract_structured to and FHIR compliant note
    """

    try:
        logger.debug(f"received: {req}")

        r = await ai_service.get_fhir(req.structured_note)
        return r

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)