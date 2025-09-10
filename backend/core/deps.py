from typing import Any
import asyncio
import httpx
from core.config import settings


class _DummyCollection:
    def __init__(self):
        self._docs = []

    def add(self, ids, documents, metadatas=None):
        for i, doc in enumerate(documents):
            self._docs.append({"id": ids[i], "text": doc, "meta": (metadatas[i] if metadatas else {})})

    def query(self, query_texts, n_results=3):
        # very naive similarity: return first n_results documents
        results = self._docs[:n_results]
        return [{"text": r["text"], "id": r["id"], "meta": r["meta"]} for r in results]


class _DummyChroma:
    def __init__(self):
        self._collections = {}

    def get_or_create_collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = _DummyCollection()
        return self._collections[name]


_chroma_client = None
_httpx_client = None


def get_chroma_client() -> Any:
    """Provide a chroma client. If chromadb is installed and configured via
    settings.CHROMA_PERSIST_DIR, you can replace the dummy with a real client.
    """
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        persist = settings.CHROMA_PERSIST_DIR
        client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist)) if persist else chromadb.Client()
        _chroma_client = client
    except Exception:
        # fallback to dummy in-memory implementation for demo / tests
        _chroma_client = _DummyChroma()

    return _chroma_client


def get_httpx_client() -> httpx.AsyncClient:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient(timeout=30.0)

    return _httpx_client


async def close_httpx_client():
    global _httpx_client
    if _httpx_client is not None:
        await _httpx_client.aclose()
        _httpx_client = None

