import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from backend.api.deps import ChromaDBSingleton

router = APIRouter()


class ConclusionCreate(BaseModel):
    stock: str
    datetime: str  # 格式: "20250918"
    prediction: str  # 如: "高开", "低开", "平开"
    confidence: float
    document: str  # 文档内容，如: "比亚迪在北美发力"


class ConclusionResponse(BaseModel):
    id: str
    stock: str
    datetime: str
    prediction: str
    confidence: float
    document: str


@router.get("/{stock}/{date}", response_model=List[ConclusionResponse])
async def get_stock_predictions(stock: str, date: str):
    """
    获取指定股票代码和日期的所有预测结果

    Args:
        stock: 股票代码，如 "sz002594"
        date: 日期，格式为 "20250918"

    Returns:
        List[ConclusionResponse]: 该股票该日期的所有预测结论
    """
    try:
        # 获取conclusions集合
        collection = ChromaDBSingleton().get_collection("conclusions")

        conds = [{"stock": {"$eq": stock}}]
        if date != "all":
            conds.append({"datetime": {"$eq": date}})
        else:
            conds.append({"datetime": {"$ne": "19001010"}})
        # 查询指定股票和日期的所有记录
        results = collection.get(
            where={
                "$and": conds
            },
            include=["documents", "metadatas"]
        )
        logging.info(str(results))
        # 格式化返回结果
        conclusions = []
        if results['ids']:
            for i in range(len(results['ids'])):
                conclusion = ConclusionResponse(
                    id=results['ids'][i],
                    stock=results['metadatas'][i]['stock'],
                    datetime=results['metadatas'][i]['datetime'],
                    prediction=results['metadatas'][i]['prediction'],
                    confidence=results['metadatas'][i]['confidence'],
                    document=results['documents'][i]
                )
                conclusions.append(conclusion)
        logging.info(str(conclusions))
        return conclusions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预测结果失败: {str(e)}")


@router.post("/add", response_model=dict)
async def add_conclusion(conclusion: ConclusionCreate):
    """
    添加或更新股票预测结论

    如果相同stock和datetime的记录已存在，则更新prediction和confidence
    如果不存在，则创建新记录

    Args:
        conclusion: ConclusionCreate对象，包含股票代码、日期、预测、置信度和文档内容

    Returns:
        dict: 包含操作结果和记录信息
    """
    try:
        # 获取conclusions集合
        collection = ChromaDBSingleton().get_collection("conclusions")

        # 查询是否存在相同stock和datetime的记录
        existing_results = collection.query(
            query_texts=[""],  # 空查询文本
            where={
                "$and": [
                    {"stock": {"$eq": conclusion.stock}},
                    {"datetime": {"$eq": conclusion.datetime}}
                ]
            },
            n_results=1
        )

        # 检查是否找到现有记录
        if existing_results['ids'] and len(existing_results['ids'][0]) > 0:
            # 记录存在，更新现有记录
            existing_id = existing_results['ids'][0][0]

            # 更新metadata
            updated_metadata = {
                "stock": conclusion.stock,
                "datetime": conclusion.datetime,
                "prediction": conclusion.prediction,
                "confidence": conclusion.confidence
            }

            # 使用upsert更新现有记录
            collection.upsert(
                documents=[conclusion.document],
                metadatas=[updated_metadata],
                ids=[existing_id]
            )

            return {
                "message": "预测结论更新成功",
                "action": "updated",
                "id": existing_id,
                "stock": conclusion.stock,
                "datetime": conclusion.datetime,
                "prediction": conclusion.prediction,
                "confidence": conclusion.confidence
            }

        else:
            # 记录不存在，创建新记录
            new_id = f"{conclusion.stock}_{conclusion.datetime}_{str(uuid.uuid4())[:8]}"

            # 准备数据
            new_documents = [conclusion.document]
            new_metadatas = [{
                "stock": conclusion.stock,
                "datetime": conclusion.datetime,
                "prediction": conclusion.prediction,
                "confidence": conclusion.confidence
            }]
            new_ids = [new_id]

            # 添加到集合
            collection.add(
                documents=new_documents,
                metadatas=new_metadatas,
                ids=new_ids
            )

            return {
                "message": "预测结论添加成功",
                "action": "created",
                "id": new_id,
                "stock": conclusion.stock,
                "datetime": conclusion.datetime,
                "prediction": conclusion.prediction,
                "confidence": conclusion.confidence
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作预测结论失败: {str(e)}")