from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from src.services.schema import ChunkingStage
from src.ai.models import EMBED_DIM

class ModelBase(DeclarativeBase):
    pass

class Document(ModelBase):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    chunking_stage: Mapped[ChunkingStage] = mapped_column(Enum(ChunkingStage), nullable=False, default=ChunkingStage.NOT_STARTED)


class DocumentChunk(ModelBase):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey(Document.id, ondelete="CASCADE"), nullable=False)
    context: Mapped[str] = mapped_column(String, nullable=False)
    chunk: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(EMBED_DIM), nullable=False)

Index(
    "ix_documents_embedding_hnsw_cos",
    DocumentChunk.embedding,
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_cosine_ops"},
    postgresql_with={"m": 16, "ef_construction": 200},
)