"""Document Service functions to upload documents to the backend API"""

from typing import Union, Dict, Any
import requests

from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)

BASE_URL = config.BACKEND_URL + "/api/v1/documents"


def upload_document(
    file: UploadedFile, 
    forced_reprocess: bool = False,
    timeout: int = 300
) -> Union[dict, str]:
    """Upload file to backend with processing status"""

    files = {"file": (file.name, file, file.type)}
    endpoint_url = BASE_URL + "/upload"
    params = {"forced_reprocess": forced_reprocess}

    try:
        response = requests.post(
            endpoint_url, 
            files=files, 
            params=params,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        return "The request timed out. Please try again later"
    except requests.ConnectionError:
        return "Unable to connect to the server. Make sure server is running"
    except requests.RequestException as e:
        logger.error("Error occurred while uploading file to backend: %s", str(e))
        return f"Upload failed: {str(e)}"


def delete_all_documents(timeout: int = 30) -> Union[dict, str]:
    """Delete all documents from backend"""

    endpoint_url = BASE_URL + "/delete-all"

    try:
        response = requests.delete(endpoint_url, timeout=timeout)
        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        return "The request timed out. Please try again later"
    except requests.ConnectionError:
        return "Unable to connect to the server. Make sure server is running"
    except requests.RequestException as e:
        logger.error("Error occurred while deleting documents from backend: %s", str(e))
        return f"Delete failed: {str(e)}"


def get_processing_status(file_hash: str, timeout: int = 10) -> Dict[str, Any]:
    """Get processing status for a document"""
    endpoint_url = BASE_URL + f"/status/{file_hash}"

    try:
        response = requests.get(endpoint_url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Error getting processing status: %s", str(e))
        return {"error": str(e)}


def list_documents(timeout: int = 10) -> Union[list, str]:
    """List all uploaded documents"""
    endpoint_url = BASE_URL + "/list"

    try:
        response = requests.get(endpoint_url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Error listing documents: %s", str(e))
        return f"List failed: {str(e)}"