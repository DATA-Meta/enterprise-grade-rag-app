from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return{"messege":"Enterprise RAG API running"}

@app.get("/health")
def root():
    return {"status": "ok"}