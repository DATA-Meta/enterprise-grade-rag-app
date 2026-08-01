from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():          # <- same name
    return{"messege":"Enterprise RAG API running"}

@app.get("/health")
def root():           # <- same name again
    return {"status": "ok"}