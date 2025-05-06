
import asyncio
from src.services.schema import DocumentChunkRead, DocumentChunkSimilarityRead, DocumentCreate, DocumentRead, DocumentUpdate
from src.db.engine import UnitOfWork

def get_documents() -> list[DocumentRead]:
    """
    Get all documents from the database.
    """
        
    with UnitOfWork() as uow:
        documents = uow.documents.get_all()

        return [DocumentRead.model_validate(doc) for doc in documents]
    
    
def get_document(document_id: int) -> DocumentRead:
    """
    Get a document by its ID.
    """
    with UnitOfWork() as uow:
        result = uow.documents.get(document_id)
        
        return DocumentRead.model_validate(result)


def update_document(document: DocumentUpdate) -> DocumentRead:
    """
    Update a document in the database.
    """
    with UnitOfWork() as uow:
        db_doc = uow.documents.update(document)
        
        return DocumentRead.model_validate(db_doc)


def create_document(document: DocumentCreate) -> DocumentRead:
    """
    Insert a document into the database.
    """

    with UnitOfWork() as uow:
        db_doc = uow.documents.create(document)
        
        return DocumentRead.model_validate(db_doc)
    
def delete_document(document_id: int) -> None:
    """
    Delete a document from the database.
    """

    with UnitOfWork() as uow:
        uow.documents.delete(document_id)

def get_similar_chunks(embeddings: list[list[float]]) -> list[DocumentChunkSimilarityRead]:
    with UnitOfWork() as uow:
        r = uow.chunks.get_similarities(embeddings)
        return [            
            DocumentChunkSimilarityRead( 
                **DocumentChunkRead.model_validate(chunk_content, from_attributes=True).model_dump(),                
                similarity=similarity,
            )
            for chunk_content, similarity in r
        ]

def get_next_chunking_document() -> DocumentRead | None:
    with UnitOfWork() as uow:
        pending = uow.documents.get_next_chunking()
        if pending:
            return DocumentRead.model_validate(pending)
        else:
            return None