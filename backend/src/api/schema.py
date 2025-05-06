from typing import Literal
from pydantic import BaseModel, Field
from fhir.resources.bundle import Bundle
from src.services.schema import AIRagResponse, DocumentRead, DumbStructuredNote

class HealthCheckResponse(BaseModel):
    status: Literal['OK'] = Field(..., description="Status of the health check")

class DocumentGetResponse(BaseModel):
    documents: list[DocumentRead] = Field(default_factory=list, description="All of the documents.")

class DocumentPostRequest(BaseModel):
    title: str = Field(..., description="Title of the document", min_length=4)
    content: str = Field(..., description="Content of the document", min_length=4)

class DocumentPostResponse(BaseModel):
    message:str = "Document accepted. Beginning chunking."

class QuestionPostRequest(BaseModel):
    question: str = Field(..., description="Question to be asked.")

class QuestionPostResponse(AIRagResponse):
    pass

class SummarizePostRequest(BaseModel):
    content: str = Field(..., description="Content of the Medical document", min_length=4)

class SummarizePostResponse(BaseModel):
    summary: str = Field(..., description="Summary of the document")

class ExtractStructuredRequest(BaseModel):
    raw_note: str = Field(..., description = "The note to extract information from.")

class ExtractStructuredResponse(DumbStructuredNote):
    pass

class ToFHIRRequest(BaseModel):
    structured_note: DumbStructuredNote = Field(..., description = "The structured note json as output from /extract_structured")

class ToFHIRResponse(Bundle):
    pass