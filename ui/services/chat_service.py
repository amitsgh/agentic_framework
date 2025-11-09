"""Chat Service functions to interact with backend API"""

from typing import Iterator, Union
import requests

from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)

BASE_URL = config.BACKEND_URL + "/api/v1/chat"

def chat_stream(query: str, timeout=None) -> Iterator[str]:
    """Interact with backend chat service and stream the response"""
    
    endpoint_url = BASE_URL + "/chat"
    
    try:
        response = requests.get(endpoint_url, params={"query": query}, stream=True, timeout=timeout)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                yield decoded_line
                
    except requests.Timeout:
        yield "The request timed out. Please try again later"
    except requests.ConnectionError:
        yield "Unable to connect to the server. Make sure server is running"
    except requests.RequestException as e:
        logger.error("Error occurred while interacting with backend: %s", str(e))
        yield "Internal Server Error"
