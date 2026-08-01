"""
Vector store: create/connect to a Qdrant collection and store/search embeddings.
"""

from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.utils.config import settings

COLLECTION_NAME = "rag_chunks"
VECTOR_SIZE = 1024  # matches mxbai-embed-large-v1 / jina-embeddings-v3 output size


@lru_cache
def get_client() -> QdrantClient:
    """Cached so we don't reconnect on every call."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


def ensure_collection(vector_size: int = VECTOR_SIZE) -> None:
    """
    Create the collection if it doesn't already exist. Safe to call every
    time the app starts — it's a no-op if the collection is already there.
    """
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_chunks(chunks: list, embeddings: list[list[float]]) -> None:
    """
    Store chunks and their embeddings in Qdrant.

    `chunks` is a list of objects with .source, .chunk_id, .text (from loader.py).
    `embeddings` is a list of vectors, same length and order as `chunks`.
    """
    client = get_client()
    ensure_collection(vector_size=len(embeddings[0]))

    points = [
        PointStruct(
            id=i,  # simple incrementing ID for now
            vector=embeddings[i],
            payload={
                "source": chunks[i].source,
                "chunk_id": chunks[i].chunk_id,
                "text": chunks[i].text,
            },
        )
        for i in range(len(chunks))
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search(query_vector: list[float], top_k: int = 3):
    """
    Return the top_k most similar chunks to the given query vector.
    """
    client = get_client()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )
    return results.points


if __name__ == "__main__":
    from src.embeddings.embedder import embed_texts
    from src.ingestion.loader import load_documents, chunk_documents

    docs = load_documents("DATA")
    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} document(s), {len(chunks)} chunk(s).")

    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)
    print(f"Generated {len(vectors)} embedding(s).")

    upsert_chunks(chunks, vectors)
    print(f"Stored {len(chunks)} chunk(s) in Qdrant collection '{COLLECTION_NAME}'.")

    # Quick sanity check: search using the first chunk's own vector.
    # It should return itself as the top result.
    hits = search(vectors[0], top_k=2)
    print("\n--- Search test (querying with the first chunk's own vector) ---")
    for hit in hits:
        print(f"Score: {hit.score:.4f} | Source: {hit.payload['source']} | Chunk: {hit.payload['chunk_id']}")