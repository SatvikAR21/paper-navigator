"""Conversational RAG chain — one chain per session, citation extraction."""

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from app.vectorstore import _get_store
from app.config import LLM_MODEL

# One chain instance per session_id — plain dict, no Redis
sessions: dict[str, ConversationalRetrievalChain] = {}
session_citations: dict[str, list[dict]] = {}


def _build_chain(where: dict | None = None) -> ConversationalRetrievalChain:
    """Create a ConversationalRetrievalChain backed by ChromaDB."""
    store = _get_store()
    search_kwargs = {"k": 5}
    if where:
        search_kwargs["filter"] = where
    retriever = store.as_retriever(search_kwargs=search_kwargs)

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )


def query(question: str, session_id: str, filters: dict | None = None) -> dict:
    """Run a question through the conversational chain, return answer + citations."""
    # Build or reuse chain (new chain if filters change)
    chain = sessions.get(session_id)
    if chain is None:
        chain = _build_chain(where=filters)
        sessions[session_id] = chain
        session_citations[session_id] = []

    result = chain({"question": question})
    answer = result["answer"]

    # Extract citations from source documents
    citations = []
    for doc in result.get("source_documents", []):
        m = doc.metadata
        cit = {
            "paper_title": m.get("paper_title", ""),
            "authors": m.get("authors", ""),
            "year": m.get("year", 0),
            "section": m.get("section", ""),
        }
        if cit not in citations:
            citations.append(cit)

    session_citations[session_id].extend(citations)
    return {"answer": answer, "citations": citations}


def get_session_citations(session_id: str) -> list[dict]:
    """Return all citations accumulated in a session."""
    return session_citations.get(session_id, [])
