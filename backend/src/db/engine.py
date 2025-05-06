from functools import cache
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.models import ModelBase
from src.db.repositories import DocumentChunkRepository, DocumentRepository

@cache
def get_engine():
    """
    Create the connection pool.
    Cached so we dont spam the db with connections.
    """
    return create_engine(
        "postgresql+psycopg://postgres:postgres@db:5432/ascertain",
        pool_pre_ping=True,
        echo = False,
        
    )

def init_db():
    with get_engine().begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
    ModelBase.metadata.create_all(bind = get_engine())

session_factory = sessionmaker( bind=get_engine(), autoflush=True )

class UnitOfWork():
    """
    Standard Unit of Work pattern. Encapsulates our repositories and provides sessioned scope. 
    """
    
    def __init__(self):
        self.session = session_factory()
        self.documents: DocumentRepository = DocumentRepository(self.session)
        self.chunks: DocumentChunkRepository = DocumentChunkRepository(self.session)
    
    def __enter__(self) -> "UnitOfWork":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        
        self.session.close()
        return False

if __name__ == "__main__":
    init_db()