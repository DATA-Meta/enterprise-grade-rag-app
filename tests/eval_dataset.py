"""
A small evaluation dataset: questions with known-correct (ground truth)
answers, based on the content of DATA/sample.txt.

Add more entries here as you ingest more documents.
"""

EVAL_QUESTIONS = [
    {
        "question": "What are the three stages of a RAG pipeline?",
        "ground_truth": (
            "The three stages of a RAG pipeline are ingestion (loading and "
            "chunking documents), retrieval (matching a query against chunks "
            "using vector similarity search), and generation (passing the "
            "retrieved chunks and question to a language model to produce "
            "an answer)."
        ),
    },
    {
        "question": "What are the two main benefits of RAG?",
        "ground_truth": (
            "RAG reduces hallucination because answers are grounded in real "
            "retrieved text, and it allows answering questions about "
            "information the model was never trained on, as long as that "
            "information is indexed in the retrieval system."
        ),
    },
]