
from enum import Enum

EMBED_DIM = 1536

class Models(Enum):
    FULL = "gpt-4.1"
    MINI = "gpt-4.1-mini"
    EMBEDDING = "text-embedding-3-small"
    LEGACY = "gpt-4o"   