from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel

from backend.api.deps import ChromaDBSingleton

router = APIRouter()

@router.get("/list")
async def get_list(limit: Optional[int] = Query(None, ge=1, description="Return top N entries (by insertion order). If omitted returns all")) -> List[Dict[str, Any]]:

    sc = ChromaDBSingleton().get_collection("info")

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


class InfoItem(BaseModel):
    id: str
    name: Optional[str] = None
    document: Optional[str] = None
    # allow arbitrary metadata keys (including non-ascii)
    metadata: Optional[Dict[str, Any]] = None

@router.post("/add")
async def add_info(items: Union[InfoItem, List[InfoItem]] = Body(..., description="A single info item or a list of items to add. Each item must include an 'id'.")) -> Dict[str, Any]:
    """Add or upsert one or more info records into the 'info' Chroma collection.

    Request body examples:
    Single item:
    {"id": "000001", "metadata": {"情绪": "中性", "置信度": 0.85}, "document": "..."}

    Or list:
    [{"id": "000001", "metadata": {"情绪": "中性"}, "document": "..."}, ...]
    """
    # normalize to a list
    sc = ChromaDBSingleton().get_collection("info")
    if items is None:
        raise HTTPException(status_code=400, detail="No items provided")

    normalized: List[InfoItem]
    if isinstance(items, list):
        normalized = items
    else:
        normalized = [items]

    if not normalized:
        raise HTTPException(status_code=400, detail="No items provided")

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for it in normalized:
        ids.append(it.id)
        # prefer explicit document, then name, then empty string
        documents.append(it.document if it.document is not None else (it.name or ""))
        # preserve metadata as-is; ensure we have a dict
        md: Dict[str, Any] = dict(it.metadata or {})
        # keep id and name in metadata for easier reads later
        if it.name and "name" not in md:
            md["name"] = it.name
        md["id"] = it.id
        metadatas.append(md)

    try:
        # use upsert to insert or update existing records
        sc.upsert(ids=ids, documents=documents, metadatas=metadatas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upsert into collection: {e}")

    return {"processed": len(ids)}
