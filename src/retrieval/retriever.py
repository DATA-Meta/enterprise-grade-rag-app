"""
Retrieval: given a plain-text question, return the most relevant stored chunks.

This ties together embeddings (turning the question into a vector) and the
vector store (searching Qdrant for similar chunks) into one simple function
that the generation step can call without knowing about either detail.
"""

from dataclasses import dataclass

from src.embeddings.embedder import embed_texts
from src.vectorstore.store import search


@dataclass
class RetrievedChunk:
    """One chunk returned from a retrieval query, with its relevance score."""
    source: str
    chunk_id: int
    text: str
    score: float


def retrieve(question: str, top_k: int = 3) -> list[RetrievedChunk]:
    """
    Embed the question and return the top_k most similar chunks from Qdrant.
    """
    # embed_texts expects a list, even for a single question
    query_vector = embed_texts([question])[0]

    hits = search(query_vector, top_k=top_k)

    return [
        RetrievedChunk(
            source=hit.payload["source"],
            chunk_id=hit.payload["chunk_id"],
            text=hit.payload["text"],
            score=hit.score,
        )
        for hit in hits
    ]


def format_context(chunks: list[RetrievedChunk]) -> str:
    """
    Combine retrieved chunks into a single text block, ready to hand to an
    LLM as context. Each chunk is labeled with its source for traceability.
    """
    parts = [f"[Source: {chunk.source}, chunk {chunk.chunk_id}]\n{chunk.text}" for chunk in chunks]
    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    test_question = "What are the three stages of a RAG pipeline?"

    results = retrieve(test_question, top_k=2)

    print(f"Question: {test_question}\n")
    print(f"Retrieved {len(results)} chunk(s):\n")

    for chunk in results:
        print(f"Score: {chunk.score:.4f} | Source: {chunk.source} | Chunk: {chunk.chunk_id}")
        print(chunk.text[:200])
        print()

    print("--- Formatted context (what would be sent to the LLM) ---")
    print(format_context(results))