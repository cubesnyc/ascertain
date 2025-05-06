import logging

_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=_FORMAT,
    handlers=[
        logging.StreamHandler()
    ],
)

logging.getLogger('httpx').disabled = True
logging.getLogger('src').setLevel(logging.DEBUG)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)