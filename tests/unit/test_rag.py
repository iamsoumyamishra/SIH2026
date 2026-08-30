"""Tests for chunking and RAG ingestion/retrieval (using a stub embedder)."""
from __future__ import annotations

from rag.chunking import chunk_text
from rag.embeddings import EmbeddingService
from rag.ingestion import IngestionService
from rag.qdrant import LocalVectorStore
from rag.retrieval import RetrievalService


class _StubEmbeddings(EmbeddingService):
    """Deterministic embeddings: simple bag-of-words hashed to vectors."""

    def embed_many(self, texts):
        out = []
        for t in texts:
            vec = [0.0] * 8
            for word in t.lower().split():
                idx = sum(ord(c) for c in word) % 8
                vec[idx] += 1.0
            out.append(vec)
        return out

    def embed(self, text):
        return self.embed_many([text])[0]


def test_chunking_splits_large_text():
    text = "\n\n".join(f"Paragraph {i} " + "word " * 200 for i in range(6))
    chunks = chunk_text(text, document_id="d1", document_name="doc.txt")
    assert len(chunks) > 1
    for c in chunks:
        assert "d1::" in c.chunk_id


def test_ingest_and_search_retrieves_relevant_chunk():
    store = LocalVectorStore()
    ing = IngestionService(embeddings=_StubEmbeddings(), store=store)
    text = (
        "Bearing vibration must stay below the limit.\n\n"
        "The bearing vibration limit is 4.5 mm/s.\n\n"
        "Engine oil should be changed annually."
    )
    ing.ingest_text(text, document_id="sop", document_name="sop.txt")

    ret = RetrievalService(embeddings=_StubEmbeddings(), store=store)
    result = ret.search("bearing vibration limit")
    assert result["count"] >= 1
    hits = result["results"]
    # The most relevant chunk should mention both terms.
    top = hits[0]["text"]
    assert "vibration" in top.lower() and "limit" in top.lower()


def test_retrieval_returns_metadata():
    store = LocalVectorStore()
    ing = IngestionService(embeddings=_StubEmbeddings(), store=store)
    ing.ingest_text(
        "Deep learning models need lots of data.",
        document_id="doc1",
        document_name="notes.txt",
        page_number=3,
        section="4.2",
        version="1.0",
        classification="internal",
    )
    ret = RetrievalService(embeddings=_StubEmbeddings(), store=store)
    r = ret.search("deep learning data")
    assert r["count"] == 1
    hit = r["results"][0]
    assert hit["document_id"] == "doc1"
    assert hit["page_number"] == 3
    assert hit["section"] == "4.2"
    assert hit["version"] == "1.0"
    assert hit["classification"] == "internal"
