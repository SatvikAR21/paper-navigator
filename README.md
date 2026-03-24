# 📄 Paper Navigator

A conversational RAG (Retrieval-Augmented Generation) system for querying academic research papers with citation tracking.

Upload PDFs → system extracts text, chunks with section metadata → stores in ChromaDB → ask natural language questions → get answers with citations → supports follow-up questions via conversation memory.

---

## Architecture

```
paper-navigator/
├── app/
│   ├── main.py          # FastAPI endpoints (upload, query, citations, papers, health)
│   ├── config.py        # Environment variables + settings
│   ├── schemas.py       # Pydantic request/response models
│   ├── ingestion.py     # PDF text extraction + section detection + chunking
│   ├── vectorstore.py   # ChromaDB operations (store, search with filters)
│   └── rag_chain.py     # Conversational chain with memory + citation extraction
├── streamlit_app.py     # Streamlit chat frontend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **Vector DB** | ChromaDB (persistent) |
| **LLM** | OpenAI GPT-3.5/4 via LangChain |
| **PDF Parsing** | PyPDF2 |
| **Chunking** | LangChain RecursiveCharacterTextSplitter |
| **RAG Chain** | LangChain ConversationalRetrievalChain |
| **Containerization** | Docker + Docker Compose |

---

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/piyushxpc7/paper-navigator.git
cd paper-navigator
cp .env.example .env
# Add your OpenAI API key to .env
```

### 2. Run with Docker

```bash
docker-compose up --build
```

- **API**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501

### 3. Run Locally (without Docker)

```bash
pip install -r requirements.txt

# Terminal 1 — Backend
uvicorn app.main:app --reload

# Terminal 2 — Frontend
streamlit run streamlit_app.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/papers/upload` | Upload a PDF with optional metadata (title, authors, year) |
| `POST` | `/query` | Ask a question with session_id and optional filters |
| `GET` | `/citations/{session_id}` | Get all citations from a conversation session |
| `GET` | `/papers` | List all indexed papers |
| `DELETE` | `/papers/{paper_id}` | Remove a paper from the index |
| `GET` | `/health` | Health check + collection stats |

### Upload a Paper

```bash
curl -X POST http://localhost:8000/papers/upload \
  -F "file=@paper.pdf" \
  -F "title=Attention Is All You Need" \
  -F "authors=Vaswani et al." \
  -F "year=2017"
```

### Query Papers

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the transformer architecture?",
    "session_id": "user123",
    "filters": {"section": "Introduction"}
  }'
```

---

## How It Works

### Ingestion Pipeline
1. **PDF Upload** → PyPDF2 extracts raw text from all pages
2. **Section Detection** → Regex matches common academic headers (Abstract, Introduction, Methodology, Results, Conclusion, etc.)
3. **Chunking** → LangChain's `RecursiveCharacterTextSplitter` chunks each section separately (1000 chars, 200 overlap)
4. **Indexing** → Chunks stored in ChromaDB with metadata: `{paper_title, authors, year, section, paper_id}`

### Query Pipeline
1. **User Question** → Optional metadata filters (year, section, author)
2. **Retrieval** → ChromaDB similarity search with `where` filters
3. **Generation** → `ConversationalRetrievalChain` generates answer using retrieved context + conversation history
4. **Citations** → Extracted from source document metadata, returned alongside the answer

### Conversation Memory
- Each `session_id` gets its own `ConversationBufferMemory`
- Follow-up questions work naturally ("What about the results?" after asking about methodology)
- Sessions stored in-memory (dict), no external dependencies

---

## Design Decisions

| Decision | Why |
|----------|-----|
| **PyPDF2** over pdfplumber | Simpler API, sufficient for text extraction |
| **Regex section detection** | Matches 90% of academic papers without NLP overhead |
| **Flat chunking** with section metadata | Simpler than parent-child; metadata filters compensate |
| **ConversationalRetrievalChain** | Single LangChain call handles retrieval + memory + generation |
| **ChromaDB `where` filters** | Built-in metadata filtering, no custom engine needed |
| **Dict-based sessions** | No Redis/DB complexity for a demo system |
| **No reranking** | ChromaDB similarity search is sufficient for this scope |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (required) |
| `LLM_MODEL` | `gpt-3.5-turbo` | LLM model name |
| `CHROMA_PERSIST_DIR` | `./chroma_data` | ChromaDB storage path |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `UPLOAD_DIR` | `./uploads` | PDF upload directory |

---

## License

MIT
