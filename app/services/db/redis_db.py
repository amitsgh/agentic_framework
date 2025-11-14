"""Redis Databse Service"""

from typing import List
import json
import uuid

import redis

from app.models.document_model import Document, DocumentMetadata
from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
from app.core.exceptions.base import DatabaseError, ValidationError
from app.core.logger import setuplog

logger = setuplog(__name__)


class RedisDB(BaseDB):
    """Redis Vector DB Class"""

    def __init__(
        self,
        redis_url: str,
        index_name: str,
        dim: int,
        distance_metric: str = "COSINE",
    ):
        self.redis_url = redis_url
        self.index_name = index_name
        self.dim = dim
        self.distance_metric = distance_metric
        self.client = None

    def _ensure_index(self):
        """Ensure redis vector index (collection) exits"""

        if not self.client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        try:
            self.client.ft(self.index_name).info()
            logger.info("Redis index '%s' already exists", self.index_name)

        except Exception:
            logger.info("Creating Redis vector index '%s'...", self.index_name)
            try:
                create_stmt = (
                    f"FT.CREATE {self.index_name} ON HASH PREFIX 1 'doc:' "
                    f"SCHEMA content TEXT metadata TEXT "
                    f"vector VECTOR HNSW 6 TYPE FLOAT32 DIM {self.dim} DISTANCE_METRIC {self.distance_metric}"
                )
                self.client.execute_command(create_stmt)
                logger.info("Index '%s' created successfully", self.index_name)

            except Exception as e:
                logger.error("Failed to create Redis index: %s", str(e))
                raise DatabaseError(f"Failed to create Redis index: {str(e)}") from e

    def connect(self) -> None:
        """Connect to Redis DB"""

        if self.client:
            logger.info("Already connected to Redis")
            return

        try:
            logger.info("Connecting to Redis at %s", self.redis_url)
            self.client = redis.Redis.from_url(self.redis_url)
            self.client.ping()
            logger.info("Connected to Redis successfully.")
            self._ensure_index()

        except Exception as e:
            logger.error("Redis connection failed: %s", str(e), exc_info=True)
            raise DatabaseError(f"Could not connect to Redis: {str(e)}") from e

    def disconnect(self) -> None:
        """Disconnect from Redis DB"""

        if self.client:
            logger.info("Disconnecting from Redis...")
            try:
                self.client.close()

            except Exception as e:
                logger.warning("Error closing Redis connection: %s", str(e))

            finally:
                self.client = None
                logger.info("Disconnected from Redis.")

        else:
            logger.warning("Redis connection already closed or not established")

    def add_documents(
        self, documents: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Embed and store documents in vector db"""

        if not self.client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        if not documents:
            raise ValidationError("No documents provided for storage")

        ids = []
        try:
            for doc in documents:
                content = doc.content
                # metadata = doc.metadata or {}
                metadata_json = json.dumps(doc.metadata.model_dump(mode='json')) or json.dumps({}) # type: ignore
                vector = embeddings.embed(content)
                vector_bytes = vector.tobytes()
                doc_id = f"doc: {uuid.uuid4()}"

                self.client.hset(
                    doc_id,
                    mapping={
                        "content": content,
                        "metadata": metadata_json,
                        "vector": vector_bytes,
                    },
                )

                ids.append(doc_id)

            logger.info("Added %d documents to Redis", len(ids))
            return ids

        except Exception as e:
            logger.error("Error adding documents to Redis: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to add documents: {str(e)}") from e

    def similarity_search(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 10
    ) -> List[Document]:
        """Search for similar document using distance metrics"""

        if not self.client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        if not query or not query.strip():
            raise ValidationError("Empty query provided for search")

        try:
            query_vector = embeddings.embed(query)
            query_bytes = query_vector.tobytes()

            search_query = f"*=>[KNN {top_k} @vector $vec AS score]"
            params = {"vec": query_bytes}

            results = self.client.ft(self.index_name).search(
                search_query, query_params=params  # type: ignore
            )
            docs = []
            for doc in results.docs:  # type: ignore
                try:
                    metadata_dict = json.loads(doc.metadata)
                    metadata = (
                        DocumentMetadata(**metadata_dict) if metadata_dict else None
                    )
                    docs.append(Document(content=doc.content, metadata=metadata))

                except Exception as e:
                    logger.warning("Error parsing document metadata: %s", str(e))
                    continue

            logger.info("Found %d matching documents", len(docs))
            return docs

        except Exception as e:
            logger.error("Search failed: %s", str(e), exc_info=True)
            raise DatabaseError(f"Similarity search failed: {str(e)}") from e

    def delete_documents_by_source(self, sources: List[str]) -> int:
        """Delete document by Sources"""

        if not self.client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        if not sources:
            raise ValidationError("No sources provided for deletion")

        try:
            keys = self.client.keys("doc:*")
            if not keys:
                logger.info("No documents found in Redis")
                return 0

            deleted = 0
            for key in keys:  # type: ignore
                doc_data = self.client.hgetall(key)
                if not doc_data:
                    continue

                try:
                    metadata_str = doc_data.get(b"metadata", b"{}").decode("utf-8")  # type: ignore
                    metadata = json.loads(metadata_str)

                    source = metadata.get("source") or metadata.get("filename")
                    if source and source in sources:
                        self.client.delete(key)
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

        if not self.client:
            raise DatabaseError(
                "Redis client is not initialized. Call connect() first."
            )

        try:
            deleted_count = 0
            keys = self.client.keys("doc:*")
            if keys:
                deleted_count = self.client.delete(*keys)  # type: ignore

            logger.info("Deleted %d documents from Redis", deleted_count)
            return deleted_count  # type: ignore

        except Exception as e:
            logger.error("Error deleting all documents: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to delete all documents: {str(e)}") from e
