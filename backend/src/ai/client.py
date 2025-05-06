from enum import Enum
import math
from typing import Type, TypeVar, overload
from openai import AsyncOpenAI, OpenAI
from openai.types import Embedding
from pydantic import BaseModel

from src.ai.models import Models
from src.ai.processing import get_token_count
from src.ai.rate_limiter import request_access
from src.env import settings

client = OpenAI(api_key = settings.OPENAI_API_KEY)
async_client = AsyncOpenAI(api_key = settings.OPENAI_API_KEY)

class OpenAIError(Exception):
    """
    Custom exception for OpenAI API errors.
    """
    def __init__(self, code: str, message: str):
        super().__init__(f"OpenAI Error: {code}: {message}")
        self.code = code
        self.message = message

@overload
async def get_response(*, input: str, instructions: str | None = None, model = Models.FULL) -> str:
    pass

StructuredOutputType = TypeVar("StructuredOutputType", bound= BaseModel)
@overload
async def get_response(*, input: str, instructions: str | None = None, model = Models.FULL, structured_output: Type[StructuredOutputType]) -> StructuredOutputType:
    pass

async def get_response(*, input: str, instructions: str | None = None, model = Models.FULL, structured_output: Type[StructuredOutputType] | None = None, timeout=20, **kwargs) -> Type[StructuredOutputType] | str:
    """
    Get a response from the OpenAI API using the provided prompt and instructions.
    
    Raises OpenAIError if the API returns an error.
    """
    n_tokens_input = get_token_count(input)
    n_tokens_instructions = get_token_count(instructions)

    await request_access( n_tokens_input + n_tokens_instructions )

    if structured_output is not None:
        response = await async_client.responses.parse(
            model= model.value,
            temperature =.5,
            input = input,
            instructions = instructions,
            timeout=timeout,
            text_format=structured_output,
            **kwargs
        )

        if response.error is not None:
            raise OpenAIError(response.error.code, response.error.message)
        
        out: StructuredOutputType = response.output_parsed
        return out
    
    else:
        response = await async_client.responses.create(
            model= model.value,
            temperature =.5,
            input = input,
            instructions = instructions,
            timeout=timeout,
            **kwargs
        )

        if response.error is not None:
            raise OpenAIError(response.error.code, response.error.message)
        
        return response.output_text



async def get_embeddings(batch_text: str | list[str]) -> list[Embedding] | list[list[Embedding]]:
    """
    Get an embedding for the given text using the OpenAI API.
    supports batching. 

    TODO: look up the max size of a batch
    """
    if isinstance(batch_text, str):
        batch_text = [batch_text]

    tokens = sum(get_token_count(it) for it in batch_text)
    tokens = int(tokens)
    await request_access(tokens)

    response = await async_client.embeddings.create(
        model=Models.EMBEDDING.value,
        input=batch_text
    )

    # TODO: error handling (there is no error field like there is in response)    
    return [it.embedding for it in response.data]