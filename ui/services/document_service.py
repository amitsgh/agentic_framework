"""Document Service functions to upload documents to the backend API"""

from typing import Union
import requests

from streamlit.runtime.uploaded_file_manager import UploadedFile

from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)

BASE_URL = config.BACKEND_URL + "/api/v1/documents"

def upload_document(file: UploadedFile, timeout=None) -> Union[dict, str]:
    """Upload file to backend"""

    files = files = {"file": (file.name, file, file.type)}
    endpoint_url = BASE_URL + "/upload"

    try:
        response = requests.post(endpoint_url, files=files, timeout=timeout)
        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        return "The request timed out. Please try again later"
    except requests.ConnectionError:
        return "Unable to connect to the server. Make sure server is running"
    except requests.RequestException as e:
        logger.error("Error occured while uploading file to backend: %s", str(e))
        return "Internal Server Error"


def delete_all_documents(timeout=None) -> Union[dict, str]:
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
        return "Internal Server Error"