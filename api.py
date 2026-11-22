from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from search import HybridSearch
from answer import answer_question

app = FastAPI(title="FinSight AI")

# load the search index once when the server starts, not on every request
searcher = HybridSearch()
documents = searcher.list_documents()


class Question(BaseModel):
    question: str
    doc: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents")
def list_documents():
    return documents


@app.post("/ask")
def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="question is empty")
    if q.doc is not None and q.doc not in documents:
        raise HTTPException(status_code=404, detail="document not found")
    return answer_question(q.question, searcher, q.doc)