import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple

def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """Extract all text from PDF. Returns (text, page_count)."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text, len(doc)

def extract_text_from_txt(file_path: str) -> Tuple[str, int]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text, 1

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for better retrieval."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def parse_document(file_path: str) -> Tuple[List[str], int]:
    """Parse document and return (chunks, page_count)."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        text, pages = extract_text_from_pdf(file_path)
    elif ext in [".txt", ".md"]:
        text, pages = extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    chunks = chunk_text(text)
    return chunks, pages