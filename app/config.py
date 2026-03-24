"""Configuration — all settings from environment variables."""

import os
from pathlib import Path

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Uploads
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
