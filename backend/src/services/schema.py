from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

class ChunkingStage(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class OrmBaseModel(BaseModel):
    model_config = {
        "from_attributes": True,
    }

class DocumentBase(OrmBaseModel):
    title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Content of the document")
    chunking_stage: ChunkingStage = Field(ChunkingStage.NOT_STARTED, description="The current chunking stage of the document.")

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    id: int = Field(..., description="ID of the document")
    title: Optional[str] = Field(None, description="Title of the document")
    content: Optional[str] = Field(None, description="Content of the document")
    chunking_stage: Optional[ChunkingStage] = Field(None, description="The current chunking stage of the document.")
    
class DocumentRead(DocumentBase):
    id: int = Field(..., description="ID of the document")

class DocumentChunkBase(OrmBaseModel):    
    document_id: int = Field(..., description="ID of the parent document.")
    context: str = Field(..., description="The surrounding context to this chunk used to generate an embedding.")
    chunk: str = Field(..., description="The text of the chunk.")
    embedding: list[float] = Field(..., description="Embedding of the chunk.")

class DocumentChunkCreate(DocumentChunkBase):
    pass

class DocumentChunkUpdate(DocumentChunkBase):
    id: int = Field(..., description="ID of the chunk")
    document_id: Optional[int] = Field(None, description="ID of the parent document")
    context: Optional[str] = Field(None, description="The surrounding context to this chunk used to generate an embedding.")
    chunk: Optional[str] = Field(None, description="The text of the chunk")
    embedding: Optional[list[float]] = Field(None, description="Embedding of the chunk")

class DocumentChunkRead(DocumentChunkBase):
    id: int = Field(..., description="ID of the chunk")

class DocumentChunkSimilarityRead(DocumentChunkRead):
    similarity: float = Field(..., description="The computed similarity of the chunk.")

class AIQuestionVariantsResponse(BaseModel):
    variants: list[str] = Field(..., description="The list of question variants.")

class AIRagContextHydrationResponse(BaseModel):
    context: str = Field(..., description = "The missing context for the given chunk. Empty string if chunk is self contained.")

class AIRagResponse(BaseModel):
    answer: str = Field(..., description= "The answer to the question.")
    citations: list[str] = Field(..., description="A list of all of the cited chunks in the answer. Every item in this list should exist as a citation in the answer.")

class CodeSystem(str, Enum):
    ICD = "ICD"
    RXNORM = "RXNORM"

class PatientInformation(BaseModel):
    first_name: Optional[str] = Field(None, description="Patient’s first name")
    last_name: Optional[str] = Field(None, description="Patient’s last name")
    dob: Optional[str] = Field(None, description="Patient’s date of birth in ISO YYYY-MM-DD format.")
    id: Optional[str] = Field(None, description="Patient’s medical-record identifier")
    gender: Optional[Literal["Male", "Female", "Other", "Unknown"]] = Field( None, description='Patient’s gender' )

class MedicalConcept(BaseModel):
    type: Literal[
        "Patient", "Condition", "Diagnosis",
        "Medication", "Treatment", "Observation", "PlanAction"
    ] = Field(
        ...,
        description="High-level category of the extracted concept. "
                    "Use the exact literals shown in the type annotation."
    )

    raw_text: str = Field(..., description = "Concept raw extracted text from the original note. ")
    name: Optional[str] = Field(..., description = "Concept system name. ")
    code: Optional[str] = Field(..., description = "Concept system code. ")
    system: Optional[CodeSystem]= Field(..., description = "Concept system. ")

class MedicalConcepts(BaseModel):
    concepts: list[MedicalConcept] = Field(default_factory=list, description="The extracted system concepts.")

class CodeLookupAction(BaseModel):
    system: Optional[CodeSystem] = Field(
        ...,
        description="The tool that should be used: "
                    "'ICD10' for an ICD lookup used for conditions/diagnoses/treatments; "
                    "'RXNORM' for and RxNorm lookup used for medications."
                    "None for everything else "
    )

    name: Optional[str] = Field(None, description = "The canonical, normalized clinical concept system name. Should be the standardized lookup term.")

class CodeLookupActions(BaseModel):
    actions: list[CodeLookupAction] = Field(default_factory=list, description="The action plans.")

class DumbStructuredNote(BaseModel):
    created_at: Optional[str] = Field(None, description = "Date of the note in ISO YYYY-MM-DD format.")
    patient: PatientInformation = Field(..., description="Patient details")
    conditions: list[MedicalConcept] = Field(default_factory=list, description="Extracted conditions.")
    diagnoses: list[MedicalConcept] = Field(default_factory=list, description="Extracted diagnoses.")
    treatments: list[MedicalConcept] = Field(default_factory=list, description="Extracted treatments.")
    medications: list[MedicalConcept] = Field(default_factory=list, description="Extracted medications.")
    observations: list[MedicalConcept] = Field(default_factory=list, description="Extracted observations.")
    plan_actions: list[MedicalConcept] = Field(default_factory=list, description="Extracted medical action plans.")


class CodeLookupResult(BaseModel):
    name: str   = Field(..., description="The system name of the code item.")
    code: str   = Field(..., description="The actual code of the code item.")
    system: CodeSystem = Field(..., description="The system used to generate this code lookup result.")

    @classmethod
    def icd(cls, *, name: str, code: str):
        return CodeLookupResult(name = name, code = code, system = CodeSystem.ICD)
    
    @classmethod
    def rxnorm(cls, *, name: str, code: str):
        return CodeLookupResult(name = name, code = code, system = CodeSystem.RXNORM)