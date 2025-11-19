"""Hybrid Chunker"""

import json
from typing import List
from pathlib import Path

from docling_core.types.doc.document import DoclingDocument

from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

from transformers import AutoTokenizer

from app.services.chunker.base import BaseChunker
from app.models.document_model import BoundingBox, Document, DocumentMetadata
from app.exceptions.base import DocumentProcessingError
from app.logger import setuplog

logger = setuplog(__name__)


class DoclingHybridChunker(BaseChunker):
    """Hybrid Chunker Class"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(model_name)
        )
        self.chunker = HybridChunker(tokenizer=self.tokenizer)

    def _extract_metadata(self, meta: dict) -> DocumentMetadata:
        """Extract & flatten the docling metadata"""

        try:
            origin = meta.get("origin", {}) or {}
            doc_items = meta.get("doc_items", []) or []
            first_item = doc_items[0] if doc_items else {}
            prov = (first_item.get("prov") or [{}])[0] if first_item else {}
            bbox = prov.get("bbox")
            bbox_model = BoundingBox(**bbox) if isinstance(bbox, dict) else None

            return DocumentMetadata(
                source=origin.get("uri"),
                page_no=prov.get("page_no"),
                content_layer=first_item.get("content_layer"),
                filename=origin.get("filename"),
                mimetype=origin.get("mimetype"),
                binary_hash=origin.get("binary_hash"),
                bbox=bbox_model,
            )

        except Exception as e:
            logger.warning("Chunk metadata extraction failed: %s", str(e))
            # Return minimal metadata instead of raising
            return DocumentMetadata()

    def chunk(self, documents: List[DoclingDocument]) -> List[Document]:
        """Chunk the data"""

        if not documents:
            raise DocumentProcessingError("No documents provided for chunking")

        all_chunks = []
        try:
            for doc in documents:
                chunk_iter = self.chunker.chunk(dl_doc=doc)

                for chunk in chunk_iter:
                    try:
                        data = chunk.model_dump_json()
                        parsed = json.loads(data)

                        content = parsed.get("text", "")
                        if not content:
                            logger.warning("Skipping chunk with empty content")
                            continue

                        metadata = self._extract_metadata(parsed.get("metadata", {}))
                        document = Document(content=content, metadata=metadata)
                        all_chunks.append(document)

                    except Exception as e:
                        logger.warning("Error processing chunk: %s", str(e))
                        continue

            if not all_chunks:
                raise DocumentProcessingError("Chunking produced no valid chunks")

            return all_chunks

        except Exception as e:
            logger.error("Error during chunking: %s", str(e), exc_info=True)
            raise DocumentProcessingError(f"Chunking failed: {str(e)}") from e