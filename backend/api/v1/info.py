from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.api.deps import ChromaDBSingleton

router = APIRouter()

class RequestDataType(BaseModel):
    stock_id: str = ""
    formatted_date: str = "19800101"
    value: float
    content: str = ""
    type: str = ""  #open_15m_avg | close

@router.post("/list/")
async def get_info(
    data: RequestDataType
):
    stock = data.stock_id
    datetime = data.formatted_date
    itype = data.type
    try:
        # 查询数据 - 只获取一条记录
        sc = ChromaDBSingleton().get_collection("info")

        results = sc.get(
            where={
                "$and": [
                    {"attached_stock_id": {"$eq": stock.lower()}},
                    {"datetime": {"$eq": datetime}},
                    {"type": {"$eq": itype}}
                ]
            },
            limit=1
        )

        # 检查是否找到数据
        if not results or not results.get('ids'):
            raise HTTPException(
                status_code=404,
                detail=f"未找到股票 {stock} 在 {datetime} 的 {itype} 数据"
            )

        # 格式化返回单条结果
        metadata = results['metadatas'][0] if results.get('metadatas') else {}

        response_data = {
            "success": True,
            "data": {
                "id": results['ids'][0],
                "stock_id": stock.lower(),
                "datetime": datetime,
                "type": itype,
                "value": metadata.get('value'),
                "content": results['documents'][0] if results.get('documents') else ""
            },
            "message": "成功获取数据"
        }

        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )

@router.post("/add/")
async def add_or_update_info(
    data: RequestDataType
):
    try:
        stock_id = data.stock_id
        formatted_date = data.formatted_date
        itype = data.type

        # 获取ChromaDB集合
        sc = ChromaDBSingleton().get_collection("info")

        # 检查是否已存在该记录
        existing_results = sc.get(
            where={
                "$and": [
                    {"attached_stock_id": {"$eq": stock_id.lower()}},
                    {"datetime": {"$eq": formatted_date}},
                    {"type": {"$eq": itype}}
                ]
            },
            limit=1
        )

        if existing_results and existing_results.get('ids'):
            # 记录已存在，更新value
            existing_id = existing_results['ids'][0]
            existing_metadata = existing_results['metadatas'][0] if existing_results.get('metadatas') else {}

            # 更新metadata中的value
            updated_metadata = existing_metadata.copy()
            updated_metadata['value'] = data.value

            # 更新记录
            sc.update(
                ids=[existing_id],
                metadatas=[updated_metadata],
                documents=[data.content] if data.content else existing_results.get('documents', [""])
            )

            response_data = {
                "success": True,
                "data": {
                    "id": existing_id,
                    "stock_id": stock_id.lower(),
                    "datetime": formatted_date,
                    "type": itype,
                    "value": data.value,
                    "content": data.content if data.content else existing_results.get('documents', [""])[0],
                    "action": "updated"
                },
                "message": f"成功更新股票 {stock_id} 在 {formatted_date} 的15分钟开盘平均价数据"
            }

        else:
            # 记录不存在，创建新记录
            import uuid

            new_id = str(uuid.uuid4())
            metadata = {
                "attached_stock_id": stock_id.lower(),
                "datetime": formatted_date,
                "type": itype,
                "value": data.value
            }

            # 添加新记录
            sc.add(
                ids=[new_id],
                metadatas=[metadata],
                documents=[data.content]
            )

            response_data = {
                "success": True,
                "data": {
                    "id": new_id,
                    "stock_id": stock_id.lower(),
                    "datetime": formatted_date,
                    "type": itype,
                    "value": data.value,
                    "content": data.content,
                    "action": "created"
                },
                "message": f"成功添加股票 {stock_id} 在 {formatted_date} 的 {itype} 数据"
            }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"server error: {str(e)}"
        )