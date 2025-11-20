"""Graph RAG API routes"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.dependency import get_graph_rag
from app.services.graph_rag.base import BaseGraphRAG
from app.utils.logger import setuplog

logger = setuplog(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


class GraphQueryRequest(BaseModel):
    """Request model for graph query"""
    query: str


class CypherQueryRequest(BaseModel):
    """Request model for Cypher query"""
    cypher: str


@router.post("/query")
async def query_graph(
    request: GraphQueryRequest,
    graph_rag: BaseGraphRAG | None = Depends(get_graph_rag),
):
    """Query graph database using natural language"""
    if not graph_rag:
        raise HTTPException(
            status_code=503,
            detail="Graph RAG service is not available. Enable it in configuration."
        )
    
    try:
        documents = graph_rag.query(request.query)
        
        # Convert documents to results
        results = []
        for doc in documents:
            results.append({
                "content": doc.content,
                "metadata": doc.metadata.model_dump(mode="json") if doc.metadata else None
            })
        
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error("Graph query failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}") from e


@router.post("/cypher")
async def execute_cypher(
    request: CypherQueryRequest,
    graph_rag: BaseGraphRAG | None = Depends(get_graph_rag),
):
    """Execute raw Cypher query"""
    if not graph_rag:
        raise HTTPException(
            status_code=503,
            detail="Graph RAG service is not available. Enable it in configuration."
        )
    
    try:
        results = graph_rag.execute_cypher(request.cypher)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error("Cypher execution failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cypher execution failed: {str(e)}") from e


@router.get("/stats")
async def get_graph_stats(
    graph_rag: BaseGraphRAG | None = Depends(get_graph_rag),
):
    """Get graph database statistics"""
    if not graph_rag:
        raise HTTPException(
            status_code=503,
            detail="Graph RAG service is not available. Enable it in configuration."
        )
    
    try:
        # Get schema info
        schema_info = graph_rag._get_schema_info() if hasattr(graph_rag, '_get_schema_info') else "N/A"
        
        # Try to get node and relationship counts
        try:
            node_labels_result = graph_rag.execute_cypher("CALL db.labels()")
            rel_types_result = graph_rag.execute_cypher("CALL db.relationshipTypes()")
            
            # Get counts
            node_count_result = graph_rag.execute_cypher("MATCH (n) RETURN count(n) as count")
            rel_count_result = graph_rag.execute_cypher("MATCH ()-[r]->() RETURN count(r) as count")
            
            node_count = node_count_result[0].get("count", 0) if node_count_result else 0
            rel_count = rel_count_result[0].get("count", 0) if rel_count_result else 0
            
            return {
                "node_count": node_count,
                "relationship_count": rel_count,
                "label_count": len(node_labels_result) if node_labels_result else 0,
                "schema_info": schema_info,
            }
        except Exception:
            return {
                "node_count": 0,
                "relationship_count": 0,
                "label_count": 0,
                "schema_info": schema_info,
            }
    except Exception as e:
        logger.error("Failed to get graph stats: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") from e

