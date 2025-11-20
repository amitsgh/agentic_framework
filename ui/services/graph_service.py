"""Graph Service functions to interact with graph database"""

from typing import Union, Dict, Any, List
import requests

from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)

BASE_URL = config.BACKEND_URL + "/api/v1/graph"


def query_graph(query: str, timeout: int = 30) -> List[Dict[str, Any]]:
    """Query graph database using natural language"""
    endpoint_url = BASE_URL + "/query"
    
    try:
        response = requests.post(
            endpoint_url,
            json={"query": query},
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.Timeout:
        logger.error("Graph query timeout")
        return []
    except requests.ConnectionError:
        logger.error("Unable to connect to graph service")
        return []
    except requests.RequestException as e:
        logger.error("Error querying graph: %s", str(e))
        return []


def get_graph_stats(timeout: int = 10) -> Dict[str, Any]:
    """Get graph database statistics"""
    endpoint_url = BASE_URL + "/stats"
    
    try:
        response = requests.get(endpoint_url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Error getting graph stats: %s", str(e))
        return {}


def execute_cypher(cypher_query: str, timeout: int = 30) -> List[Dict[str, Any]]:
    """Execute raw Cypher query"""
    endpoint_url = BASE_URL + "/cypher"
    
    try:
        response = requests.post(
            endpoint_url,
            json={"cypher": cypher_query},
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        logger.error("Error executing Cypher: %s", str(e))
        return []

