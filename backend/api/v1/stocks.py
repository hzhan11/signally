import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.api.deps import ChromaDBSingleton

router = APIRouter()

@router.get("/list")
async def get_list():

    sc = ChromaDBSingleton().get_collection("stocks")

    """Query all stocks and return as list of dictionaries"""
    results = sc.get(include=["metadatas", "documents"])

    logging.info(f"{str(results)}")

    stocks = []
    for i, doc_id in enumerate(results['ids']):
        stock = {
            "id": doc_id,
            "metadata": results['metadatas'][i],
            "document": results['documents'][i]
        }
        stocks.append(stock)
    return stocks