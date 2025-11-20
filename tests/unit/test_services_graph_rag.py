"""Unit tests for Graph RAG services"""

import pytest
from unittest.mock import Mock, patch
from app.services.graph_rag.llm_graph_rag import LLMGraphRAG
from app.models.document_model import Document, DocumentMetadata
from app.exceptions import DatabaseError


class TestLLMGraphRAG:
    """Tests for LLMGraphRAG"""

    @pytest.fixture
    def graph_rag(self, mock_llm):
        """Create LLMGraphRAG instance"""
        return LLMGraphRAG(
            llm=mock_llm,
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password",
            database="neo4j",
        )

    def test_text_to_cypher(self, graph_rag, mock_llm):
        """Test converting text to Cypher"""
        mock_llm.model_response.return_value = "MATCH (n) RETURN n LIMIT 10"
        cypher = graph_rag.text_to_cypher("Find all nodes")
        assert "MATCH" in cypher
        assert "RETURN" in cypher

    @patch("neo4j.GraphDatabase.driver")
    def test_execute_cypher(self, mock_driver, graph_rag):
        """Test executing Cypher query"""
        mock_session = Mock()
        mock_record = Mock()
        mock_record.items.return_value = [("name", "John")]
        mock_session.run.return_value = [mock_record]
        mock_driver_instance = Mock()
        mock_driver_instance.session.return_value.__enter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance
        graph_rag._driver = mock_driver_instance
        results = graph_rag.execute_cypher("MATCH (n) RETURN n")
        assert len(results) > 0

    def test_query(self, graph_rag, mock_llm):
        """Test query method"""
        mock_llm.model_response.return_value = "MATCH (n) RETURN n"
        with patch.object(graph_rag, "execute_cypher") as mock_execute:
            mock_execute.return_value = [{"name": "John", "age": 30}]
            docs = graph_rag.query("Find all people")
            assert len(docs) > 0
            assert isinstance(docs[0], Document)

    def test_get_schema_info(self, graph_rag):
        """Test getting schema information"""
        with patch.object(graph_rag, "execute_cypher") as mock_execute:
            mock_execute.side_effect = [
                [{"label": "Person"}],
                [{"relationshipType": "KNOWS"}],
            ]
            schema = graph_rag._get_schema_info()
            assert "Person" in schema or len(schema) > 0

