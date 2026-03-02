import chromadb
from sentence_transformers import SentenceTransformer
from app.config import settings
from typing import List

# Initialize once
_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
_encoder = SentenceTransformer("all-MiniLM-L6-v2")

def get_collection(doc_id: int):
    return _client.get_or_create_collection(f"doc_{doc_id}")

def add_chunks(doc_id: int, chunks: List[str]):
    """Embed and store chunks for a document."""
    collection = get_collection(doc_id)
    embeddings = _encoder.encode(chunks).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, embeddings=embeddings, ids=ids)

def search_chunks(doc_id: int, query: str, n_results: int = 5) -> List[str]:
    """Find the most relevant chunks for a query."""
    collection = get_collection(doc_id)
    query_embedding = _encoder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)
    return results["documents"][0] if results["documents"] else []

def delete_document_vectors(doc_id: int):
    try:
        _client.delete_collection(f"doc_{doc_id}")
    except Exception:
        pass