from asyncio import Semaphore
import asyncio
from collections import deque
from dataclasses import dataclass
import random
import time
from src.env import settings

MAX_TOKENS_MIN = 200000
MAX_REQ_MIN = 20

@dataclass(frozen=True)
class LogItem:
    timestamp: float
    num_tokens: int

request_log: deque[LogItem] = deque()
lock = asyncio.Lock()

async def request_access(num_tokens: int) -> None:
    while True:
        now = time.perf_counter()

        async with lock:
            while request_log and (now - request_log[0].timestamp) > 60:
                request_log.popleft()
            
            tokens_last_minute = sum(li.num_tokens for li in request_log)
            requests_last_minute = len(request_log)

            if tokens_last_minute + num_tokens < MAX_TOKENS_MIN and requests_last_minute < MAX_REQ_MIN:
                request_log.append(LogItem(now, num_tokens))
                return
            
            else:
                wait_time = 60 - (now - request_log[0].timestamp) + 5 # for some buffer
        
        await asyncio.sleep(wait_time) 
           


    