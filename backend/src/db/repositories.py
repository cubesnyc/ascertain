from http.client import PROCESSING
from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, cast, column, desc, func, select, true, union_all, update, values
import sqlalchemy
import sqlalchemy.orm

from src.ai.models import EMBED_DIM
from src.services.schema import ChunkingStage, DocumentChunkCreate, DocumentChunkRead, DocumentChunkSimilarityRead, DocumentChunkUpdate, DocumentCreate, DocumentUpdate
from src.db.models import Document, DocumentChunk

class DocumentNotFoundError(Exception):
    """
    Exception raised when a document is not found.
    """
    def __init__(self, document_id: int):
        super().__init__(f"Document with ID {document_id} not found.")
        self.document_id = document_id

class DocumentChunkNotFoundError(Exception):
    """
    Exception raised when a document chunk is not found.
    """
    def __init__(self, chunk_id: int):
        super().__init__(f"Document chunk with ID {chunk_id} not found.")
        self.chunk_id = chunk_id

class DocumentChunkRepository:
    """
    Document chunk repository for CRUD operations.
    """

    def __init__(self, session: sqlalchemy.orm.Session):
        self.session = session
    
    def get(self, document_id: int) -> DocumentChunk:
        """
        Get a document chunk by its ID.
        """

        result = self.session.get(DocumentChunk, document_id)
        if not result:
            raise DocumentChunkNotFoundError(document_id)
        return result
    
    def create(self, chunk: DocumentChunkCreate) -> DocumentChunk:
        """
        Insert a document chunk into the database.
        """

        db_chunk = DocumentChunk(**chunk.model_dump())
        self.session.add(db_chunk)
        self.session.flush()

        return db_chunk
    
    def update(self, chunk: DocumentChunkUpdate) -> DocumentChunk:
        """
        Update a document chunk in the database.
        """

        db_chunk = self.session.get(Document, chunk.id)

        if not db_chunk:
            raise DocumentChunkNotFoundError(chunk.id)

        for key, value in chunk.model_dump(exclude={"id"}, exclude_unset=True).items():
            setattr(db_chunk, key, value)

        self.session.flush()
        return db_chunk
    
    def  get_similarities(self, embeddings: list[list[float]], limit = 10) -> list[tuple[DocumentChunk, float]]:
        """
        accepts a list of embeddings and returns the closest matching chunks
        """

        # build the temp table with question embeddings
        v = (
            values(
                column("q_idx", Integer),
                column("q_embedding", Vector(EMBED_DIM))
            )
            .data((i, embedding) for i, embedding in enumerate(embeddings))
            .alias()
        )

        # cross join the question embeddings with the 
        crossed = (
            select(
                DocumentChunk.id, 
                DocumentChunk.embedding.cosine_distance( cast(v.c.q_embedding, Vector(EMBED_DIM)) ).label("similarity")
            )
            .select_from(
                v.join(
                    DocumentChunk,
                    true(),
                )
            )
            .order_by("similarity")
            .limit(limit * len(embeddings))
            .subquery()
        )
            
        best = (
            select(
                crossed.c.id,
                func.min(crossed.c.similarity).label("similarity")
            )
            .group_by(crossed.c.id)    
            .subquery()                    
        )

        final = (
            select(DocumentChunk, best.c.similarity)
            .join(best, DocumentChunk.id == best.c.id)
            .order_by(best.c.similarity)
            .limit(limit)
        )

        return self.session.execute(final).all()
    
    

class DocumentRepository:
    """
    Document repository for CRUD operations.
    """

    def __init__(self, session: sqlalchemy.orm.Session):
        self.session = session

    
    def get_all(self) -> list[Document]:
        """
        Get all documents from the database.
        """

        sql = select(Document)
        result = self.session.execute(sql).scalars().all()

        return result
        
    def get(self, document_id: int) -> Document:
        """
        Get a document by its ID.
        """

        result = self.session.get(Document, document_id)
        if not result:
            raise DocumentNotFoundError(document_id)
        return result

    def get_next_chunking(self,) -> Document | None:
        """
        Get the next document to process for chunking
        """

        stmt_sq = (
            select(Document.id)
            .where(Document.chunking_stage == ChunkingStage.NOT_STARTED)
            .with_for_update(skip_locked=True)
            .limit(1)
            .subquery()
        )

        stmt = (
            update(Document)
            .where(Document.id == stmt_sq.c.id)
            .values(chunking_stage = ChunkingStage.IN_PROGRESS)
            .returning(Document)
            .execution_options(synchronize_session="fetch") 
        )

        r = self.session.execute(stmt)
        document = r.scalars().first()
        return document

    def update(self, document: DocumentUpdate) -> Document:
        """
        Update a document in the database.
        """

        db_doc = self.session.get(Document, document.id)

        if not db_doc:
            raise DocumentNotFoundError(document.id)

        for key, value in document.model_dump(exclude={"id"}, exclude_unset=True).items():
            setattr(db_doc, key, value)

        self.session.flush()
        return db_doc

    def create(self, document: DocumentCreate) -> Document:
        """
        Insert a document into the database.
        """

        db_doc = Document(**document.model_dump())
        self.session.add(db_doc)

        self.session.flush()
        return db_doc
        
    def delete(self, document_id: int) -> None:
        """
        Delete a document from the database.
        """
        db_doc = self.session.get(Document, document_id)
        
        if not db_doc:
            raise DocumentNotFoundError(document_id)
        
        self.session.delete(db_doc)
        self.session.flush()        