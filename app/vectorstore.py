"""ChromaDB operations — index, search with metadata filters, stats, delete."""

import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from app.config import CHROMA_PERSIST_DIR

COLLECTION_NAME = "papers"

_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
_embeddings = OpenAIEmbeddings()


def _get_store() -> Chroma:
    return Chroma(
        client=_client,
        collection_name=COLLECTION_NAME,
        embedding_function=_embeddings,
    )


def index_paper(paper_id: str, chunks: list[dict]) -> int:
    """Add chunks to ChromaDB. Returns number of chunks stored."""
    store = _get_store()
    texts = [c["text"] for c in chunks]
    metadatas = [{**c["metadata"], "paper_id": paper_id} for c in chunks]
    ids = [f"{paper_id}_{i}" for i in range(len(chunks))]
    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return len(chunks)


def search(query: str, k: int = 5, where: dict | None = None) -> list:
    """Similarity search with optional metadata filters."""
    store = _get_store()
    kwargs = {"k": k}
    if where:
        kwargs["filter"] = where
    return store.similarity_search(query, **kwargs)


def get_stats() -> dict:
    """Return collection count."""
    col = _client.get_or_create_collection(COLLECTION_NAME)
    return {"total_chunks": col.count()}


def get_all_papers() -> list[dict]:
    """List unique papers with metadata."""
    col = _client.get_or_create_collection(COLLECTION_NAME)
    data = col.get(include=["metadatas"])
    papers: dict[str, dict] = {}
    for meta in data["metadatas"]:
        pid = meta["paper_id"]
        if pid not in papers:
            papers[pid] = {
                "paper_id": pid,
                "title": meta["paper_title"],
                "authors": meta["authors"],
                "year": meta["year"],
                "chunk_count": 0,
            }
        papers[pid]["chunk_count"] += 1
    return list(papers.values())


def delete_paper(paper_id: str) -> bool:
    """Remove all chunks for a paper."""
    col = _client.get_or_create_collection(COLLECTION_NAME)
    existing = col.get(where={"paper_id": paper_id})
    if not existing["ids"]:
        return False
    col.delete(ids=existing["ids"])
    return True
