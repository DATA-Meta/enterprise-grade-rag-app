"""
Embedding generation.

Primary: Jina AI's embedding API (jina-embeddings-v3) — used when JINA_API_KEY
is set in .env.
Fallback: local mxbai-embed-large-v1 model via sentence-transformers — used
automatically when no Jina API key is configured, so this works offline with
zero signup while you're still learning.
"""

from functools import lru_cache

import requests

from src.utils.config import settings

JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL_NAME = "jina-embeddings-v3"
LOCAL_MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"


@lru_cache
def _get_local_model():
    """
    Load the local fallback model once and cache it, since loading it from
    disk/downloading it is slow and we don't want to repeat that per call.
    """
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(LOCAL_MODEL_NAME)


def _embed_with_jina(texts: list[str]) -> list[list[float]]:
    response = requests.post(
        JINA_API_URL,
        headers={
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
        },
        json={"model": JINA_MODEL_NAME, "input": texts},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    # Jina returns results in the same order as the input list.
    return [item["embedding"] for item in data["data"]]


def _embed_with_local_model(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Turn a list of text strings into a list of embedding vectors.

    Uses the Jina API if a key is configured; otherwise falls back to the
    local model automatically.
    """
    if settings.jina_api_key:
        return _embed_with_jina(texts)
    return _embed_with_local_model(texts)


if __name__ == "__main__":
    sample_texts = [
        "Retrieval-Augmented Generation combines search with language models.",
        "The weather today is sunny with a light breeze.",
    ]
    vectors = embed_texts(sample_texts)

    print(f"Generated {len(vectors)} embedding(s).")
    print(f"Each embedding has {len(vectors[0])} dimensions.")
    print(f"First 5 values of first embedding: {vectors[0][:5]}")