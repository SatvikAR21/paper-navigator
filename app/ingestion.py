"""PDF ingestion — extract text, detect sections via regex, chunk with metadata."""

import re
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

# Regex for common academic section headers
SECTION_PATTERN = re.compile(
    r"^(?:\d+\.?\s*)?(Abstract|Introduction|Background|Related Work|"
    r"Methodology|Methods|Method|Approach|Experiments?|Results?|"
    r"Discussion|Conclusion|Conclusions|References|Acknowledgements?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_text(pdf_path: str) -> str:
    """Read all pages from a PDF and return concatenated text."""
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def detect_sections(text: str) -> list[dict]:
    """Split text into sections based on regex-matched headers."""
    matches = list(SECTION_PATTERN.finditer(text))
    if not matches:
        return [{"section": "Full Text", "content": text}]

    sections = []
    for i, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append({"section": name, "content": content})
    return sections


def chunk_paper(
    text: str, paper_title: str, authors: str, year: int
) -> list[dict]:
    """Chunk each section separately, attaching paper metadata to every chunk."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    sections = detect_sections(text)
    chunks = []
    for sec in sections:
        splits = splitter.split_text(sec["content"])
        for s in splits:
            chunks.append(
                {
                    "text": s,
                    "metadata": {
                        "paper_title": paper_title,
                        "authors": authors,
                        "year": year,
                        "section": sec["section"],
                    },
                }
            )
    return chunks
