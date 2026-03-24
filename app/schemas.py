"""Pydantic request/response models — flat, no custom validators."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    session_id: str
    filters: dict | None = None  # e.g. {"year": 2023, "section": "Results"}


class Citation(BaseModel):
    paper_title: str
    authors: str
    year: int
    section: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


class UploadResponse(BaseModel):
    paper_id: str
    title: str
    chunks_created: int


class PaperInfo(BaseModel):
    paper_id: str
    title: str
    authors: str
    year: int
    chunk_count: int
