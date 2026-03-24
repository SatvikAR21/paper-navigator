"""FastAPI endpoints — upload, query, citations, papers, health."""

import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from app.config import UPLOAD_DIR
from app.schemas import (
    QueryRequest, QueryResponse, UploadResponse, PaperInfo, Citation,
)
from app.ingestion import extract_text, chunk_paper
from app.vectorstore import index_paper, get_all_papers, delete_paper, get_stats
from app.rag_chain import query as rag_query, get_session_citations

app = FastAPI(title="Research Paper Navigator", version="1.0.0")


@app.post("/papers/upload", response_model=UploadResponse)
async def upload_paper(
    file: UploadFile = File(...),
    title: str = Form("Untitled"),
    authors: str = Form("Unknown"),
    year: int = Form(2024),
):
    """Accept a PDF, extract text, chunk with metadata, store in ChromaDB."""
    paper_id = str(uuid.uuid4())[:8]
    pdf_path = Path(UPLOAD_DIR) / f"{paper_id}.pdf"

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text(str(pdf_path))
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    chunks = chunk_paper(text, paper_title=title, authors=authors, year=year)
    count = index_paper(paper_id, chunks)
    return UploadResponse(paper_id=paper_id, title=title, chunks_created=count)


@app.post("/query", response_model=QueryResponse)
async def query_papers(req: QueryRequest):
    """Ask a question with optional metadata filters. Returns answer + citations."""
    result = rag_query(req.question, req.session_id, req.filters)
    citations = [Citation(**c) for c in result["citations"]]
    return QueryResponse(answer=result["answer"], citations=citations)


@app.get("/citations/{session_id}", response_model=list[Citation])
async def get_citations(session_id: str):
    """All citations used across a session's conversation."""
    return [Citation(**c) for c in get_session_citations(session_id)]


@app.get("/papers", response_model=list[PaperInfo])
async def list_papers():
    """List all indexed papers with metadata."""
    return [PaperInfo(**p) for p in get_all_papers()]


@app.delete("/papers/{paper_id}")
async def remove_paper(paper_id: str):
    """Remove a paper's chunks from ChromaDB."""
    if not delete_paper(paper_id):
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"status": "deleted", "paper_id": paper_id}


@app.get("/health")
async def health():
    """Alive check with collection stats."""
    stats = get_stats()
    return {"status": "healthy", **stats}
