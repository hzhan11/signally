from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List

from core.deps import get_chroma_client

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), source: str = Form("uploaded"), chroma=Depends(get_chroma_client)):
    """Receive a file, perform naive text splitting and persist to Chroma.

    This is a minimal example: real ingestion should handle file types, encoding,
    chunk overlapping, metadata, deduplication, and batching.
    """
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Only utf-8 text files supported in demo")

    # very simple splitter: split on paragraphs
    chunks: List[str] = [p.strip() for p in text.split("\n\n") if p.strip()]

    # persist to chroma: this demo assumes chroma client has a simple collection API
    collection = chroma.get_or_create_collection(name="documents")
    ids = [f"{source}-{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "filename": file.filename} for _ in chunks]

    collection.add(ids=ids, documents=chunks, metadatas=metadatas)

    return {"inserted": len(chunks), "ids": ids}


@router.post("/text")
async def ingest_text(text: str = Form(...), source: str = Form("inline"), chroma=Depends(get_chroma_client)):
    # reuse logic from upload
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    collection = chroma.get_or_create_collection(name="documents")
    ids = [f"{source}-{i}" for i in range(len(chunks))]
    metadatas = [{"source": source} for _ in chunks]
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return {"inserted": len(chunks)}

