"""Integration tests for graph API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestGraphEndpoints:
    """Integration tests for graph endpoints"""

    @patch("app.api.v1.graph.get_graph_rag")
    def test_graph_query(self, mock_graph_rag, client):
        """Test graph query endpoint"""
        mock_graph = Mock()
        mock_doc = Mock()
        mock_doc.content = "Test result"
        mock_doc.metadata = None
        mock_graph.query.return_value = [mock_doc]
        mock_graph_rag.return_value = mock_graph
        response = client.post(
            "/api/v1/graph/query",
            json={"query": "Find all people"},
        )
        assert response.status_code == 200
        assert "results" in response.json()

    @patch("app.api.v1.graph.get_graph_rag")
    def test_graph_query_not_available(self, mock_graph_rag, client):
        """Test graph query when service not available"""
        mock_graph_rag.return_value = None
        response = client.post(
            "/api/v1/graph/query",
            json={"query": "test"},
        )
        assert response.status_code == 503

    @patch("app.api.v1.graph.get_graph_rag")
    def test_execute_cypher(self, mock_graph_rag, client):
        """Test Cypher execution endpoint"""
        mock_graph = Mock()
        mock_graph.execute_cypher.return_value = [{"result": "data"}]
        mock_graph_rag.return_value = mock_graph
        response = client.post(
            "/api/v1/graph/cypher",
            json={"cypher": "MATCH (n) RETURN n LIMIT 10"},
        )
        assert response.status_code == 200

    @patch("app.api.v1.graph.get_graph_rag")
    def test_get_graph_stats(self, mock_graph_rag, client):
        """Test graph stats endpoint"""
        mock_graph = Mock()
        mock_graph.execute_cypher.return_value = [
            {"count": 10},
            {"count": 5},
            [{"label": "Person"}],
        ]
        mock_graph._get_schema_info.return_value = "Schema info"
        mock_graph_rag.return_value = mock_graph
        response = client.get("/api/v1/graph/stats")
        assert response.status_code == 200
        assert "node_count" in response.json()


