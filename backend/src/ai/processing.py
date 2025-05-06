from typing import Generator

import tiktoken

from src.ai.models import Models

def normalize_text(text):
    """
    Normalize the text by removing special characters. 
    """
    return ' '.join(text.split()).lower()

def get_token_count(text: str | None) -> int:
    """
    Get the number of tokens in the text assuming a token is roughly 3.5 characters (for margin)
    """
    if not text: return 0

    # https://github.com/openai/tiktoken
    return len(tiktoken.get_encoding("o200k_base").encode(text)) * 1.1 # slight margin of error

def generate_naive_chunks(text: str, chunk_size: int = 2**9, overlap: int = 2**7) -> Generator[str, None, None]:
    """
    Naively chunk the text into smaller pieces with a minor overlap. 
    """

    i = 0
    while i < len(text):
        text_chunk = text[i : i + chunk_size]
        yield text_chunk
        i += chunk_size - overlap
        