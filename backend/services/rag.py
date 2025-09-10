from typing import List, Any
from core.logging import logger


async def retrieve_context(query: str, chroma_client, top_k: int = 3) -> List[Any]:
    """Retrieve top_k documents from the vector DB and return simple context list.

    This demo function expects chroma_client to expose get_or_create_collection(...).query(...)
    or the dummy implementation from deps.py.
    """
    logger.debug("Retrieving context for query: %s", query)
    collection = chroma_client.get_or_create_collection(name="documents")

    # chroma's query semantics differ between real client and dummy; adapt accordingly
    try:
        # real chroma client may use .query or .get
        results = collection.query(query_texts=[query], n_results=top_k)
    except Exception:
        # fallback to dummy .query
        results = collection.query(query_texts=[query], n_results=top_k)

    # normalize results to list of dicts with text and metadata
    context = []
    for r in results:
        if isinstance(r, dict) and "text" in r:
            context.append({"id": r.get("id"), "text": r.get("text"), "meta": r.get("meta")})
        else:
            # try to handle list-style responses from some clients
            try:
                context.append({"id": r["id"], "text": r["document"], "meta": r.get("metadata")})
            except Exception:
                # best-effort fallback
                context.append({"text": str(r)})

    return context

