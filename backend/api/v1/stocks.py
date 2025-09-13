from fastapi import APIRouter

from backend.common.deps import get_chroma_client

router = APIRouter()
c = get_chroma_client()
sc = c.get_or_create_collection("stocks")

@router.get("/list")
async def get_list():
    """Query all stocks and return as list of dictionaries"""
    results = sc.get(include=["documents", "metadatas"])

    stocks = []
    for i, doc_id in enumerate(results['ids']):
        stock = {
            "id": doc_id,
            "name": results['documents'][i],
            "metadata": results['metadatas'][i]
        }
        stocks.append(stock)
    return stocks


