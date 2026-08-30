# ADR-004: Local RAG with Vector-Store Abstraction

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

AGENTS.md requires local retrieval (Qdrant + local embeddings) with rich chunk
metadata and citations. Qdrant is not always running during development, so the
system needs a local fallback that is not a cloud service.

## Decision

1. `EmbeddingService` calls embeddings only through `ModelProvider.embeddings()`
   (the local Ollama embedding model, e.g. `nomic-embed-text`).
2. `VectorStore` (abstract) has two real implementations:
   - `QdrantVectorStore` (production path, via the official client)
   - `LocalVectorStore` (in-process numpy cosine store — fully local, not cloud)
   `settings.rag_backend` selects which; if Qdrant is unreachable it degrades
   explicitly to the local store (never to a cloud).
3. Every chunk retains metadata (`document_id`, `document_name`, `page_number`,
   `section`, `version`, `classification`, `chunk_id`) enabling citations.

## Consequences

- RAG works immediately with the already-installed embedding model and local
  store, and uses Qdrant when available.
- Retrieval returns metadata for source citations in the UI/answers.
- Embedding and store use the same local stack regardless of file type.
