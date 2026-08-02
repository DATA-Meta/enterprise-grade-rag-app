from fastapi import FastAPI
from pydantic import BaseModel

from src.generation.generator import answer_question

app = FastAPI(title="Enterprise Agentic RAG API")


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    blocked: bool
    block_reason: str | None = None


@app.get("/")
def read_root():
    return {"message": "Enterprise RAG API running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result = answer_question(request.question)
    return QueryResponse(
        question=result.question,
        answer=result.answer,
        sources=result.sources,
        blocked=result.blocked,
        block_reason=result.block_reason,
    )