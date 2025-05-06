import asyncio
from pathlib import Path
from pprint import pprint
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.bundle import Bundle

from src.services.coders import run_code_lookup_action
from src.services.documents import get_next_chunking_document, get_similar_chunks, update_document
from src.ai.models import Models
from src.ai.processing import generate_naive_chunks
from src.db.engine import UnitOfWork
from src.services.schema import AIQuestionVariantsResponse, AIRagContextHydrationResponse, AIRagResponse, ChunkingStage, CodeLookupAction, CodeLookupActions, CodeSystem, DocumentChunkCreate, DocumentRead, DocumentUpdate, DumbStructuredNote, MedicalConcept, MedicalConcepts
from src.utils import retry
from src.ai.client import get_embeddings, get_response
from src.ai.prompts import get_chunk_prompt_input, get_chunk_prompt_instructions, get_question_variants_input, get_question_variants_instructions, get_rag_qa_input, get_rag_qa_instructions, get_structured_note_input, get_structured_note_instructions, get_structured_note_step1_input, get_structured_note_step1_instructions, get_structured_note_step2_input, get_structured_note_step2_instructions, get_structured_note_step4_input, get_structured_note_step4_instructions, get_summarize_prompt_input, get_summarize_prompt_instructions
from src._logging import get_logger

logger = get_logger(__name__)

async def summarize_text(text: str) -> str:
    """
    Summarize the given text using OpenAI API.
    """
    instructions = get_summarize_prompt_instructions()
    input = get_summarize_prompt_input(text)
    response = await get_response(input=input, instructions = instructions)
    return response

async def get_question_answer(question: str) -> AIRagResponse:
    """
    We generate several versions of the question and perform a cosign sim search. 10 results are kept and used to generate the answer.
    Reranker is not used by design. 
    """
    logger.debug(f"get_question_answer: {question}")

    q_variants_prompt_instructions = get_question_variants_instructions()
    q_variants_prompt_input = get_question_variants_input(question)
    q_variants = await get_response(input = q_variants_prompt_input, instructions=q_variants_prompt_instructions, structured_output = AIQuestionVariantsResponse) 
    
    logger.debug(f"----------VARIANTS----------\nQ: {question}\nV: {q_variants.variants}")
    
    q_variant_embeddings = await get_embeddings([question] + q_variants.variants)
    best_chunks = get_similar_chunks(q_variant_embeddings)
    logger.debug(f"----------RETRIEVED CHUNKS----------")
    for it in best_chunks:
        logger.debug(f"---------chunk------------\nsimilarity: {it.similarity * 100 // 1}\ncontext: {it.context}\nchunk:{it.chunk}\n")

    answer = await get_response(input = get_rag_qa_input(question, best_chunks), instructions = get_rag_qa_instructions(), structured_output= AIRagResponse)
    
    logger.debug(answer)
    
    # attach cited chunks
    best_chunks_map = {str(chunk.id): chunk for chunk in best_chunks}

    return answer.model_copy(update = {"citations": [f"[{c_id}]: {best_chunks_map[c_id].chunk}" for c_id in answer.citations if c_id in best_chunks_map]})

async def get_structured_note_agentic(raw_note: str) -> DumbStructuredNote:
    """
    ## A more agentic version of structured note construction. 
    This is extremely overexaggerated. After step 1 we already know which system (icd, rxnorm) api calls to make based on the mapped category. 
    For illustrative purposes we instead play dumb and instead have the LLM decide to mimic a tool calling flow. 

    - step1: extract raw concepts
    - step2: ask llm to for an action plan for each concept
    - step3: call apis
    - step4: build structured note
    """

    # extract raw concepts
    logger.debug("Extracting raw concepts")
    extracted_concept_instructions = get_structured_note_step1_instructions()
    extracted_concept_input = get_structured_note_step1_input(raw_note)
    extracted_concepts = await get_response(input = extracted_concept_input, instructions = extracted_concept_instructions, structured_output=MedicalConcepts)

    logger.debug(extracted_concepts)

    @retry
    async def lookup_concept(concept: MedicalConcept):
        logger.debug(f"Identifying lookup for {concept.raw_text}")
        # get the lookup action. in reality we already know it but for demonstration.
        lookup_action_instructions = get_structured_note_step2_instructions()        
        lookup_action_input = get_structured_note_step2_input(concept)
        lookup_action = await get_response(input = lookup_action_input, instructions= lookup_action_instructions, structured_output=CodeLookupAction)

        if lookup_action.system is None:
            return concept
        
        else:
            logger.debug(f"Performing lookup for {concept.raw_text}")
            # perform api lookup
            lookup_result = await run_code_lookup_action(lookup_action)
            if lookup_result is None:
                return concept
            else:
                return concept.model_copy(update = lookup_result.model_dump())
            
    logger.debug("Starting lookup agents")
    hydrated_concepts = [lookup_concept(it) for it in extracted_concepts.concepts]
    hydrated_concepts = await asyncio.gather(*hydrated_concepts)

    # stitch the results into the final structured note
    logger.debug("Finalizing structured note")
    step4_instructions = get_structured_note_step4_instructions()
    step4_input = get_structured_note_step4_input(hydrated_concepts)
    step4_out = await get_response(input = step4_input, instructions = step4_instructions, structured_output=DumbStructuredNote)

    return step4_out


async def get_fhir(note: DumbStructuredNote) -> Bundle:
    """
    Given the structured note output, we want to convert it to an FHIR compliant bundle
    We use the fhir library as advised. 
    
    I tried to map all of the fields I thought were obvious, and made reasonable guesses for the required ones. 
    """

    logger.debug(f"get_fhir-note: {note}")

    # https://www.hl7.org/fhir/patient.html
    accepted_genders = {'male', 'female', 'other', 'unknown'}

    patient = Patient(
        id = note.patient.id,
        name = [{
            "given": [note.patient.first_name],
            "family": note.patient.last_name,            
        }],
        gender = note.patient.gender if note.patient.gender in accepted_genders else "unknown",
        birthDate= note.patient.dob
    )

    # https://www.hl7.org/fhir/condition.html
    conditions = [
        Condition(
            subject= {"reference": f"Patient/{note.patient.id}"},
            clinicalStatus = {"text": "active"},
            recordedDate = note.created_at,
            code= { 
                "text": it.name,
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "code": it.code,
                }]
            }
        )
        for it in note.conditions + note.diagnoses
    ]

    # https://www.hl7.org/fhir/medicationstatement.html
    medications = [
        MedicationStatement(
            subject= {"reference": f"Patient/{note.patient.id}"},
            dateAsserted = note.created_at,
            status = "active",
            medication= { 
                "concept": {
                    "text": it.name,
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": it.code,
                    }]
                }
            }
        )
        for it in note.medications
    ]

    return Bundle.model_construct(
        type="collection",
        entry = (
            [{"resource": patient}]
            + [{"resource": r} for r in conditions + medications]
        )
    )

async def chunk_document(document: DocumentRead) -> None:
    """
    Master function that kicks off the chunking process. 

    Returns: a list of contextually aware chunks.
    """
    logger.info(f"Chunking started {document.id}...")

    # title could be relevant, we dont want to throw it out
    full_doc = document.title + "\n\n" + document.content

    # split these up to take advantage of caching. 
    instructions = get_chunk_prompt_instructions(full_doc)
    chunks = [chunk for chunk in generate_naive_chunks(full_doc, chunk_size=2**10)]
    
    @retry
    async def get_context_aware_chunk(id: int, chunk: str) -> AIRagContextHydrationResponse: 
        """
        given a raw chunk, we return the derived context given the full document
        """
        logger.debug(f"processing chunk #{document.id:04d}-{id:04d}")
        input = get_chunk_prompt_input(chunk)
        response = await get_response( instructions=instructions, input=input, model=Models.MINI, structured_output=AIRagContextHydrationResponse )
        return response

    contexts = await asyncio.gather(
        *[get_context_aware_chunk(i, input) for i, input in enumerate(chunks)]
    )

    # combine the contexts and chunks
    hydrated_chunks = [
        f"{context.context}\n\n{chunk}" for chunk, context in zip(chunks, contexts)
    ]

    logger.debug("generating embeddings")

    # use the contextualized chunks to generate the embeddings
    embeddings = await get_embeddings(hydrated_chunks)

    logger.debug("persisting embeddings")

    # persist
    with UnitOfWork() as uow:
        for i, (chunk, context) in enumerate(zip(chunks, contexts)):
            embedding = embeddings[i]
            document_chunk = DocumentChunkCreate(
                document_id=document.id,
                context = context.context,
                chunk=chunk,
                embedding= embedding,
            )
            uow.chunks.create(document_chunk)

    logger.info(f"Chunking complete {document.id}")

async def document_chunking_worker():
    while True:
        try:
            # the db has the queued up documents, we pull one and lock it 
            pending_doc = get_next_chunking_document()

            if pending_doc is not None:
                try:
                    await chunk_document( pending_doc )
                    update_document(DocumentUpdate(id = pending_doc.id, chunking_stage=ChunkingStage.COMPLETED))

                except Exception as ex:
                    logger.exception(f"Failed chunking document {pending_doc.id}", ex)
                    update_document(DocumentUpdate(id = pending_doc.id, chunking_stage=ChunkingStage.FAILED))

            else:
                await asyncio.sleep(2)
        
        except Exception as ex:
            logger.exception("Document chunking worker error", ex)
            await asyncio.sleep(2)



if __name__ == "__main__":
    # file = Path("/workspaces/backend/resources/amgn_earnings.txt")
    # document = DocumentRead(id=1, title="AMGN earnings call", content=file.read_text())
    # asyncio.run(chunk_document(document))

    # variants = asyncio.run(get_question_answer("What was Amgen's 2025 revenue guidance?"))

    # raw_note = Path("/workspaces/backend/resources/soap_02.txt").read_text()
    # asyncio.run(get_structured_note_agentic(raw_note))
    # print(note.model_dump_json())

    # fhir_note = asyncio.run(get_fhir(note))
    # print(fhir_note)
    pass