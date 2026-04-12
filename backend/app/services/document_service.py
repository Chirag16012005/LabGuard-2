from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a student submission."""

    id: str
    filename: str
    content: str


class InMemoryDocumentStore:
    """Minimal production-ready in-memory document store."""

    MAX_DOCUMENTS = 10_000
    MAX_CONTENT_LENGTH = 50_000_000  # 50MB limit for documents

    def __init__(self) -> None:
        self._docs: Dict[str, Document] = {}

    def add_document(self, doc_id: str, filename: str, content: str) -> Document:
        if not doc_id or not isinstance(doc_id, str):
            raise ValueError("doc_id must be a non-empty string")
        if not filename or not isinstance(filename, str):
            raise ValueError("filename must be a non-empty string")
        if content is None or not isinstance(content, str):
            raise ValueError("content must be a non-empty string")

        if len(self._docs) >= self.MAX_DOCUMENTS and doc_id not in self._docs:
            raise RuntimeError("document store capacity exceeded")

        if len(content) > self.MAX_CONTENT_LENGTH:
            logger.warning(
                "Document %s content length %d exceeds MAX_CONTENT_LENGTH=%d; truncating",
                doc_id,
                len(content),
                self.MAX_CONTENT_LENGTH,
            )
            content = content[: self.MAX_CONTENT_LENGTH]

        doc = Document(id=doc_id, filename=filename, content=content)
        self._docs[doc_id] = doc
        return doc

    def get_document(self, doc_id: str) -> Optional[Document]:
        if not isinstance(doc_id, str):
            raise TypeError("doc_id must be a string")
        return self._docs.get(doc_id)

    def list_documents(self) -> List[Document]:
        return list(self._docs.values())

    def remove_document(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    def clear(self) -> None:
        self._docs.clear()


__all__ = ["Document", "InMemoryDocumentStore"]

