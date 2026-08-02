"""
Reranking: take retrieved chunks and re-score them for relevance using
Jina AI's Reranker API, which is more precise than raw vector similarity.
"""

import requests

from src.utils.config import settings
from src.retrieval.retriever import RetrievedChunk

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"
JINA_RERANK_MODEL = "jina-reranker-v2-base-multilingual"


def rerank(question: str, chunks: list[RetrievedChunk], top_k: int = 3) -> list[RetrievedChunk]:
    """
    Re-score `chunks` against `question` using Jina's reranker, and return
    the top_k most relevant, with updated scores.
    """
    if not chunks:
        return chunks

    documents = [chunk.text for chunk in chunks]

    response = requests.post(
        JINA_RERANK_URL,
        headers={
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": JINA_RERANK_MODEL,
            "query": question,
            "documents": documents,
            "top_n": top_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    results = response.json()["results"]

    reranked = []
    for result in results:
        original_chunk = chunks[result["index"]]
        reranked.append(
            RetrievedChunk(
                source=original_chunk.source,
                chunk_id=original_chunk.chunk_id,
                text=original_chunk.text,
                score=result["relevance_score"],
            )
        )

    return reranked


if __name__ == "__main__":
    from src.retrieval.retriever import retrieve

    test_question = "What are the three stages of a RAG pipeline?"

    initial_results = retrieve(test_question, top_k=5)
    print(f"--- Before reranking ({len(initial_results)} chunks) ---")
    for chunk in initial_results:
        print(f"Score: {chunk.score:.4f} | Chunk: {chunk.chunk_id}")

    reranked_results = rerank(test_question, initial_results, top_k=3)
    print(f"\n--- After reranking (top {len(reranked_results)}) ---")
    for chunk in reranked_results:
        print(f"Score: {chunk.score:.4f} | Chunk: {chunk.chunk_id}")