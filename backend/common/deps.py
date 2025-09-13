from typing import Any

from backend.common.config import settings


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
    """Provide a chroma client.
    """
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client
    try:
        import chromadb
        client = chromadb.HttpClient(host=settings.CHROMA_SERVER_IP,port=settings.CHROMA_SERVER_PORT)
        _chroma_client = client
    except Exception:
        # fallback to dummy in-memory implementation for demo / tests
        _chroma_client = _DummyChroma()

    return _chroma_client

