"""LLM-based Graph RAG Service with Neo4j"""

from typing import List, Dict, Any, Optional
import json

from neo4j import GraphDatabase, Driver, Session

from app.models.document_model import Document, DocumentMetadata
from app.services.graph_rag.base import BaseGraphRAG
from app.services.llm.base import BaseLLM
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


class LLMGraphRAG(BaseGraphRAG):
    """Graph RAG using LLM for Text-to-Cypher translation with Neo4j"""

    def __init__(
        self,
        llm: BaseLLM,
        graph_schema: str | None = None,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ):
        self.llm = llm
        self.graph_schema = graph_schema or self._default_schema()

        # Neo4j connection parameters
        self.uri = uri or config.NEO4J_URI
        self.user = user or config.NEO4J_USER
        self.password = password or config.NEO4J_PASSWORD
        self.database = database or config.NEO4J_DATABASE

        self._driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Neo4j database"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connection
            if self._driver:
                self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", self.uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j: %s", str(e), exc_info=True)
            self._driver = None
            raise

    def _get_session(self) -> Session:
        """Get Neo4j session"""
        if self._driver is None:
            self._connect()
        if self._driver is None:
            raise RuntimeError("Neo4j driver not available")
        return self._driver.session(database=self.database)

    def close(self) -> None:
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Closed Neo4j connection")

    def text_to_cypher(self, query: str) -> str:
        """Convert natural language to Cypher query"""
        try:
            # Get current schema from database if available
            schema_info = self._get_schema_info()

            prompt = f"""Convert the following natural language query into a Cypher query for a Neo4j graph database.

Graph Schema:
{self.graph_schema}

Current Database Schema:
{schema_info}

Natural Language Query: {query}

Generate a valid Cypher query. Only return the Cypher query, no explanations. Do not include markdown code blocks:"""

            messages = [{"role": "user", "message": prompt}]
            cypher = self.llm.model_response(messages).strip()

            # Clean up response (remove markdown code blocks if present)
            if "```" in cypher:
                lines = cypher.split("\n")
                cypher = "\n".join(
                    [
                        line
                        for line in lines
                        if not (
                            line.strip().startswith("```")
                            or line.strip().startswith("cypher")
                        )
                    ]
                )

            # Remove leading/trailing whitespace
            cypher = cypher.strip()

            logger.info("Generated Cypher query: %s", cypher[:100])
            return cypher

        except Exception as e:
            logger.warning("Text-to-Cypher failed: %s", str(e))
            # Return a simple fallback query
            return f"MATCH (n) WHERE toLower(toString(n.name)) CONTAINS toLower('{query}') RETURN n LIMIT 10"

    def execute_cypher(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute Cypher query and return results"""
        if self._driver is None:
            logger.error("Neo4j driver not connected")
            return []

        try:
            with self._get_session() as session:
                result = session.run(cypher_query)  # type: ignore[arg-type]

                # Convert Neo4j records to dictionaries
                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert Neo4j Node/Relationship to dict
                        if hasattr(value, "items"):
                            record_dict[key] = dict(value.items())
                        elif hasattr(value, "__dict__"):
                            record_dict[key] = str(value)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)

                logger.info("Executed Cypher query, returned %d records", len(records))
                return records

        except Exception as e:
            logger.error("Cypher execution failed: %s", str(e), exc_info=True)
            return []

    def query(self, query: str) -> List[Document]:
        """Query graph database using natural language"""
        try:
            cypher = self.text_to_cypher(query)
            results = self.execute_cypher(cypher)

            # Convert graph results to Documents
            documents = []
            for idx, result in enumerate(results):
                # Format result as readable text
                content = self._format_result(result)
                metadata = DocumentMetadata(
                    source="graph_db",
                    filename=f"graph_query_result_{idx}",
                    page_no=idx,
                    content_layer=None,
                    mimetype=None,
                    binary_hash=None,
                    bbox=None,
                )
                documents.append(Document(content=content, metadata=metadata))

            logger.info("Graph RAG query returned %d documents", len(documents))
            return documents

        except Exception as e:
            logger.error("Graph RAG query failed: %s", str(e), exc_info=True)
            return []

    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format Neo4j result as readable text"""
        try:
            parts = []
            for key, value in result.items():
                if isinstance(value, dict):
                    # Node or Relationship
                    if "labels" in value or "type" in value:
                        parts.append(f"{key}: {json.dumps(value, indent=2)}")
                    else:
                        parts.append(f"{key}: {json.dumps(value)}")
                else:
                    parts.append(f"{key}: {value}")
            return "\n".join(parts)
        except Exception:
            return str(result)

    def _get_schema_info(self) -> str:
        """Get current schema information from Neo4j"""
        if self._driver is None:
            return "Database not connected"

        try:
            with self._get_session() as session:
                # Get node labels
                node_labels_result = session.run("CALL db.labels()")
                node_labels = [record["label"] for record in node_labels_result]

                # Get relationship types
                rel_types_result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in rel_types_result]

                schema_info = f"Node Labels: {', '.join(node_labels) if node_labels else 'None'}\n"
                schema_info += f"Relationship Types: {', '.join(rel_types) if rel_types else 'None'}"

                return schema_info
        except Exception as e:
            logger.warning("Failed to get schema info: %s", str(e))
            return "Schema information unavailable"

    def _default_schema(self) -> str:
        """Default graph schema description"""
        return """
Node types:
- Person: {name, age, occupation}
- Organization: {name, type}
- Document: {title, content, date}

Relationship types:
- KNOWS: Person -> Person
- WORKS_FOR: Person -> Organization
- AUTHORED: Person -> Document
- RELATED_TO: Document -> Document
"""
