"""Redis Databse Service"""

from typing import List, Optional, cast
import json
import uuid

import redis

from app.models.document_model import Document, DocumentMetadata
from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.exceptions import DatabaseError, ValidationError
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


class RedisDB(BaseDB):
    """Redis Vector DB Class"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        index_name: Optional[str] = None,
        dim: Optional[int] = None,
        distance_metric: Optional[str] = None,
    ):
        self.redis_url = redis_url or config.REDIS_URL
        self.index_name = index_name or config.COLLECTION_NAME
        self.dim = dim if dim is not None else config.EMBEDDING_DIMENSIONS
        self.distance_metric = distance_metric or config.DISTANCE_METRIC
        self._client: Optional[redis.Redis] = None

    def _build_index_creation_command(self) -> str:
        """Build Redis FT.CREATE command for vector index"""
        return (
            f"FT.CREATE {self.index_name} ON HASH PREFIX 1 '{config.REDIS_DOC_KEY_PREFIX}' "
            f"SCHEMA content TEXT metadata TEXT "
            f"vector VECTOR HNSW 6 TYPE FLOAT32 DIM {self.dim} DISTANCE_METRIC {self.distance_metric}"
        )

    def _ensure_index(self):
        """Ensure redis vector index (collection) exits"""

        if not self._client:
            logger.critical("Redis client is not initialized. Call connect() first.")
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        try:
            self._client.ft(self.index_name).info()
            logger.info("Redis index '%s' already exists", self.index_name)
            logger.debug("Redis index '%s' verified successfully", self.index_name)

        except Exception:
            logger.info("Creating Redis vector index '%s'...", self.index_name)
            logger.debug("Index creation parameters: dim=%s, metric=%s", self.dim, self.distance_metric)
            try:
                create_command = self._build_index_creation_command()
                logger.debug("Executing index creation command: %s", create_command)
                self._client.execute_command(create_command)
                logger.info("Index '%s' created successfully", self.index_name)
                logger.debug("Redis index creation completed")

            except Exception as e:
                logger.critical("Failed to create Redis index: %s", str(e), exc_info=True)
                raise DatabaseError(f"Failed to create Redis index: {str(e)}") from e

    def connect(self) -> None:
        """Connect to Redis DB"""

        try:
            logger.info("Connecting to Redis at %s", self.redis_url)
            logger.debug("Redis connection parameters: index=%s, dim=%s, metric=%s", 
                        self.index_name, self.dim, self.distance_metric)
            self._client = redis.Redis.from_url(self.redis_url)
            self._client.ping()
            logger.info("Connected to Redis successfully.")
            logger.debug("Redis ping successful, ensuring index exists...")
            self._ensure_index()

        except Exception as e:
            logger.critical("Redis connection failed: %s", str(e), exc_info=True)
            logger.debug("Redis connection failed at URL: %s", self.redis_url)
            raise DatabaseError(f"Could not connect to Redis: {str(e)}") from e

    def get_client(self) -> redis.Redis:
        if self._client is None:
            self.connect()

        return cast(redis.Redis, self._client)

    def disconnect(self) -> None:
        """Disconnect from Redis DB"""

        if self._client:
            logger.info("Disconnecting from Redis...")
            try:
                self._client.close()

            except Exception as e:
                logger.warning("Error closing Redis connection: %s", str(e))

            finally:
                self._client = None
                logger.info("Disconnected from Redis.")

        else:
            logger.warning("Redis connection already closed or not established")

    def add_documents(
        self, documents: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Embed and store documents in vector db"""

        if not self._client:
            logger.critical("Redis client is not initialized. Call connect() first.")
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        if not documents:
            logger.warning("No documents provided for storage")
            raise ValidationError("No documents provided for storage")

        logger.debug("Starting to add %d documents to Redis", len(documents))
        ids = []
        try:
            for idx, doc in enumerate(documents):
                logger.debug("Processing document %d/%d", idx + 1, len(documents))
                content = doc.content
                # metadata = doc.metadata or {}
                metadata_json = json.dumps(doc.metadata.model_dump(mode="json")) or json.dumps({})  # type: ignore
                logger.debug("Generating embedding for document %d (content length: %d)", idx + 1, len(content))
                vector = embeddings.embed(content)
                vector_bytes = vector.tobytes()
                doc_id = f"{config.REDIS_DOC_KEY_PREFIX}{uuid.uuid4()}"
                logger.debug("Storing document %d with ID: %s", idx + 1, doc_id)

                self._client.hset(
                    doc_id,
                    mapping={
                        "content": content,
                        "metadata": metadata_json,
                        "vector": vector_bytes,
                    },
                )

                ids.append(doc_id)

            logger.info("Added %d documents to Redis", len(ids))
            logger.debug("Document addition completed successfully")
            return ids

        except Exception as e:
            logger.error("Error adding documents to Redis: %s", str(e), exc_info=True)
            logger.debug("Failed to add %d documents, successfully added %d", len(documents), len(ids))
            raise DatabaseError(f"Failed to add documents: {str(e)}") from e

    def similarity_search(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 10
    ) -> List[Document]:
        """Search for similar document using distance metrics"""

        if not self._client:
            logger.critical("Redis client is not initialized. Call connect() first.")
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        if not query or not query.strip():
            logger.warning("Empty query provided for search")
            raise ValidationError("Empty query provided for search")

        logger.debug("Starting similarity search with query length: %d, top_k: %d", len(query), top_k)
        try:
            logger.debug("Generating query embedding...")
            query_vector = embeddings.embed(query)
            query_bytes = query_vector.tobytes()

            search_query = f"*=>[KNN {top_k} @vector $vec AS score]"
            params = {"vec": query_bytes}
            logger.debug("Executing Redis search query: %s", search_query)

            results = self._client.ft(self.index_name).search(
                search_query, query_params=params  # type: ignore
            )
            logger.debug("Redis search returned %d results", len(results.docs) if hasattr(results, 'docs') else 0) # type: ignore
            docs = []
            for idx, doc in enumerate(results.docs):  # type: ignore
                try:
                    metadata_dict = json.loads(doc.metadata)
                    metadata = (
                        DocumentMetadata(**metadata_dict) if metadata_dict else None
                    )
                    docs.append(Document(content=doc.content, metadata=metadata))
                    logger.debug("Parsed document %d/%d successfully", idx + 1, len(results.docs))  # type: ignore

                except Exception as e:
                    logger.warning("Error parsing document metadata: %s", str(e))
                    logger.debug("Failed to parse metadata for document %d", idx + 1)
                    continue

            logger.info("Found %d matching documents", len(docs))
            logger.debug("Similarity search completed successfully")
            return docs

        except Exception as e:
            logger.error("Search failed: %s", str(e), exc_info=True)
            logger.debug("Search failed for query: %s", query[:50] if len(query) > 50 else query)
            raise DatabaseError(f"Similarity search failed: {str(e)}") from e

    def delete_documents_by_source(self, sources: List[str]) -> int:
        """Delete document by Sources"""

        if not self._client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        if not sources:
            raise ValidationError("No sources provided for deletion")

        try:
            keys = self._client.keys(config.REDIS_DOC_KEY_PATTERN)
            if not keys:
                logger.info("No documents found in Redis")
                return 0

            deleted = 0
            for key in keys:  # type: ignore
                doc_data = self._client.hgetall(key)
                if not doc_data:
                    continue

                try:
                    metadata_str = doc_data.get(b"metadata", b"{}").decode("utf-8")  # type: ignore
                    metadata = json.loads(metadata_str)

                    source = metadata.get("source") or metadata.get("filename")
                    if source and source in sources:
                        self._client.delete(key)
                        deleted += 1

                except Exception as e:
                    logger.warning("Error parsing metadata for key %s: %s", key, e)
                    continue

            logger.info("Deleted %d documents from Redis by source", deleted)
            return deleted

        except Exception as e:
            logger.error(
                "Error deleting documents by source: %s", str(e), exc_info=True
            )
            raise DatabaseError(
                f"Failed to delete documents by source: {str(e)}"
            ) from e

    def delete_all(self) -> int:
        """Delete all documents"""

        if not self._client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        try:
            deleted_count = 0
            keys = self._client.keys(config.REDIS_DOC_KEY_PATTERN)
            if keys:
                deleted_count = self._client.delete(*keys)  # type: ignore

            logger.info("Deleted %d documents from Redis", deleted_count)
            return deleted_count  # type: ignore

        except Exception as e:
            logger.error("Error deleting all documents: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to delete all documents: {str(e)}") from e
