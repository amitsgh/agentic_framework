"""Redis Databse Service"""

from typing import List

import json
import uuid
from typing import List

import redis

from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
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
            raise RuntimeError("Redis client is not initialized. Call connect() first.")

        try:
            self.client.ft(self.index_name).info()
            logger.info("Redis index '%s' already exists", self.index_name)

        except Exception:
            logger.info("Creating Redis vector index '%s'...", self.index_name)
            create_stmt = (
                f"FT.CREATE {self.index_name} ON HASH PREFIX 1 'doc:' "
                f"SCHEMA content TEXT metadata TEXT "
                f"vector VECTOR HNSW 6 TYPE FLOAT32 DIM {self.dim} DISTANCE_METRIC {self.distance_metric}"
            )
            self.client.execute_command(create_stmt)
            logger.info("Index '%s' created successfully", self.index_name)

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
            logger.error("Redis connection failed: %s", str(e))
            raise ConnectionError(f"Could not connect to Redis: {e}")

    def disconnect(self) -> None:
        """Disconnect from Redis DB"""

        if self.client:
            logger.info("Disconnecting from Redis...")
            self.client.close()
            self.client = None
            logger.info("Disconnected from Redis.")

        else:
            logger.warning("Redis connection already closed or not established")

    def add_documents(
        self, documents: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Embed and store documents in vector db"""

        if not self.client:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")

        ids = []
        for doc in documents:
            content = doc.content
            metadata = doc.metadata or {}
            vector = embeddings.embed(content)
            vector_bytes = vector.tobytes()
            doc_id = f"doc: {uuid.uuid4()}"

            self.client.hset(
                doc_id,
                mapping={
                    "content": content,
                    "metadata": json.dumps(metadata),
                    "vector": vector_bytes,
                },
            )

            ids.append(doc_id)

        logger.info("Added %d documents to Redis", len(ids))
        return ids

    def similarity_search(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 10
    ) -> List[Document]:
        """Search for similar document using distance metrics"""

        if not self.client:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")

        query_vector = embeddings.embed(query)
        query_bytes = query_vector.tobytes()

        search_query = f"*=>[KNN {top_k} @vector $vec AS score]"
        params = {"vec": query_bytes}

        try:
            results = self.client.ft(self.index_name).search(
                search_query, query_params=params  # type: ignore
            )
            docs = []
            for doc in results.docs:  # type: ignore
                metadata = json.loads(doc.metadata)
                docs.append(Document(content=doc.content, metadata=metadata))

            logger.info("Found %d matching documents", len(docs))
            return docs

        except Exception as e:
            logger.error("Search failed: %s", str(e))
            raise

    def delete_documents_by_source(self, sources: List[str]) -> int:
        """Detele document by Sources"""

        if not self.client:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")

        if not sources:
            logger.warning("No sources provided for deletion.")
            raise

        try:
            keys = self.client.keys("doc:*")
            if not keys:
                logger.info("No documents found in Redis")
                return False

            deleted = 0
            for key in keys: # type: ignore
                doc_data = self.client.hgetall(key)
                if not doc_data:
                    continue

                try:
                    metadata_str = doc_data.get(b"metadata", b"{}").decode("utf-8") # type: ignore
                    metadata = json.loads(metadata_str)

                    source = metadata.get("source") or metadata.get("filename")
                    if source and source in sources:
                        self.client.delete(key)
                        deleted += 1

                except Exception as e:
                    logger.warning("Error parsing metadata for key %s: %s", key, e)
                    continue

            logger.info("Deleted %d documents from Redis by source", deleted)
            return deleted > 0

        except Exception as e:
            logger.error("Error deleting documents by source: %s", str(e))
            return False

    def delete_all(self) -> int:
        """Delete all documents"""

        if not self.client:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")

        deleted_count = 0
        keys = self.client.keys("doc:*")
        if keys:
            deleted_count = self.client.delete(*keys)  # type: ignore

        logger.info("Deleted %d documents from Redis", deleted_count)
        return deleted_count  # type: ignore
