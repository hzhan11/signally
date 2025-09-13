from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any

from backend.common.deps import get_chroma_client

router = APIRouter()
c = get_chroma_client()
sc = c.get_or_create_collection("info")

@router.get("/list")
async def get_list(limit: Optional[int] = Query(None, ge=1, description="Return top N entries (by insertion order). If omitted returns all")) -> List[Dict[str, Any]]:
    # retrieve raw data from collection
    # Note: Chroma `get` does not accept 'ids' in the include list; request only allowed fields
    results = sc.get(include=["documents", "metadatas"]) or {}
    ids = results.get("ids", [])
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])

    records: List[Dict[str, Any]] = []
    length = max(len(ids), len(docs), len(metas))
    for i in range(length):
        rec: Dict[str, Any] = {}
        if i < len(metas) and isinstance(metas[i], dict):
            rec.update(metas[i])
        if i < len(ids):
            rec["id"] = ids[i]
        if i < len(docs):
            # keep the original document text under 'document', and also set 'name' if available
            rec.setdefault("document", docs[i])
            rec.setdefault("name", docs[i])
        records.append(rec)

    if limit is not None:
        return records[:limit]
    return records
