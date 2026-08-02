"""
LLM Gateway: routes chat completion calls through Portkey to Groq,
using a Portkey virtual key so the real Groq key never lives in this code.
"""

from portkey_ai import Portkey

from src.utils.config import settings

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def get_client() -> Portkey:
    return Portkey(
        api_key=settings.portkey_api_key,
        virtual_key=settings.groq_virtual_key,
    )


def generate_answer(question: str, context: str, model: str = DEFAULT_MODEL) -> str:
    """
    Ask the LLM to answer `question` using only the provided `context`.
    """
    client = get_client()

    system_prompt = (
        "You are a helpful assistant. Answer the user's question using ONLY "
        "the information in the provided context. If the answer isn't in the "
        "context, say you don't have enough information to answer."
    )

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    test_context = (
        "A typical RAG pipeline has three stages: ingestion, where documents are "
        "loaded and split into chunks; retrieval, where a user's question is "
        "matched against those chunks using vector similarity search; and "
        "generation, where the retrieved chunks are passed to a language model "
        "along with the question to produce a final answer."
    )
    test_question = "What are the three stages of a RAG pipeline?"

    answer = generate_answer(test_question, test_context)
    print(f"Question: {test_question}\n")
    print(f"Answer: {answer}")