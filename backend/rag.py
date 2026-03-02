"""
RAG: On application startup the backend processes faq.txt, chunks the text,
generates vector embeddings (OpenAI), and stores them in a lightweight local
vector store (in-memory array with cosine similarity). When a user asks a
policy-related question, the AI retrieves relevant chunks and uses them to generate its answer.
"""
import os
from pathlib import Path

import numpy as np

FAQ_PATH = Path(__file__).parent / "faq.txt"

# In-memory store: (chunks, embeddings matrix)
_chunks: list[str] = []
_embeddings: np.ndarray | None = None


def get_embeddings(texts: list[str]) -> list[list[float]]:
    import openai
    client = openai.OpenAI()
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def load_and_chunk_faq() -> list[str]:
    content = FAQ_PATH.read_text(encoding="utf-8")
    raw_paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks = []
    for p in raw_paragraphs:
        if len(p.split()) <= 400:
            chunks.append(p)
        else:
            chunks.extend(chunk_text(p, chunk_size=400, overlap=50))
    return chunks


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b) + 1e-10)
    return float(np.dot(a_norm, b_norm))


def init_rag():
    """Load FAQ, chunk, embed, and store in memory. Idempotent. Skips if OPENAI_API_KEY missing."""
    global _chunks, _embeddings
    if _chunks and _embeddings is not None:
        return
    try:
        chunks = load_and_chunk_faq()
        if not chunks:
            return
        embeddings = get_embeddings(chunks)
        _chunks = chunks
        _embeddings = np.array(embeddings, dtype=np.float32)
    except Exception as e:
        import sys
        print(f"RAG init skipped (set OPENAI_API_KEY in backend/.env): {e}", file=sys.stderr)


def retrieve(query: str, top_k: int = 4) -> list[str]:
    """Return top_k most relevant FAQ chunks for the query."""
    if not _chunks or _embeddings is None:
        return []
    query_emb = np.array(get_embeddings([query])[0], dtype=np.float32)
    scores = np.array([_cosine_similarity(query_emb, _embeddings[i]) for i in range(len(_chunks))])
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [_chunks[i] for i in top_indices]
