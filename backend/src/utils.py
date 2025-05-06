

from asyncio import sleep
from functools import wraps

from src._logging import get_logger


logger = get_logger(__name__)

def retry(func):
    """
    Decorator to retry a function call if it raises an exception.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        for i in range(3):  # Retry up to 3 times
            try:
                return await func(*args, **kwargs)
            except Exception as e:                
                logger.warning("Retrying task...")
                if i == 2:
                    raise
                
            await sleep(2 ** i)
    return wrapper