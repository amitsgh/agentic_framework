"""Chat Service functions to interact with backend API"""

from typing import Iterator
import requests

from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)

BASE_URL = config.BACKEND_URL + "/api/v1/chat"


def chat_stream(
    query: str,
    model_name: str = "ollama/llama2",
    use_rag: bool = True,
    timeout: int = 300
) -> Iterator[str]:
    """Interact with backend chat service and stream the response"""
    
    endpoint_url = BASE_URL + "/chat"
    params = {
        "query": query,
        "model_name": model_name,
        "use_rag": use_rag,
    }
    
    try:
        response = requests.get(
            endpoint_url,
            params=params,
            stream=True,
            timeout=timeout
        )
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
        yield f"Error: {str(e)}"
