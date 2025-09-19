import datetime
import uuid
import os

import pytest
from fastapi import HTTPException

# 禁用ChromaDB的遥测功能
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'

from chromadb import HttpClient
from chromadb.config import Settings
from backend.common import logger_client, sconfig

# 创建客户端时明确禁用遥测
client = HttpClient(
    host="localhost",
    port=sconfig.settings.DB_PORT,
    settings=Settings(anonymized_telemetry=False)
)

def test_add_info_data():
    sc = client.get_or_create_collection("info")

    info_data = [
        {"id":"88171217-db93-49fa-8034-773078563013", "datetime":"2025-09-10 22:02:44", "content":""},
    ]

    for one in info_data:
        metadata = {
            "id": one["id"],
            "attached_stock_id": "002594",
            "datetime": one["datetime"],
            "type": "news"
        }

        sc.upsert(
            ids=[one["id"]],
            documents=[one["content"]],
            metadatas=[metadata]
        )

def test_delete_info_data():
    client.delete_collection("info")

def test_add_log_connection():
    sc = client.get_collection("log")
    print(sc.count(), sc.name)

def test_delete_info_log():
    client.delete_collection("log")

def test_add_stock():
    new_documents = ["比亚迪股份有限公司的主营业务是以新能源汽车为主的汽车业务、手机部件及组装业务，二次充电电池及光伏业务，同时利用自身的技术优势积极拓展城市轨道交通业务领域。公司的主要产品是汽车业务、手机部件、组装业务、二次充电电池、光伏业务。"]  # 文档内容
    new_metadatas = [{"name": "比亚迪"}]  # 元数据
    new_ids = ["sz002594"]  # 唯一ID

    sc = client.get_or_create_collection("stocks")

    sc.add(
        documents=new_documents,
        metadatas=new_metadatas,
        ids=new_ids
    )

def test_stock_clean():
    sc = client.get_or_create_collection("stocks")
    sc.delete(ids=["sz002594"])

def test_get_stocks():
    sc = client.get_collection("stocks")
    print(sc.count())

def test_append_conclusion():

    sc = client.get_or_create_collection("conclusions")

    new_documents = ["比亚迪在北美发力"]  # 文档内容
    new_metadatas = [{"stock": "sz002594","datetime":"20250918","prediction":"高开","confidence":0.8}]
    new_ids = [f"sz002594_{str(uuid.uuid4())}"]  # 唯一ID

    sc.add(
        documents=new_documents,
        metadatas=new_metadatas,
        ids=new_ids
    )

def test_clear_conclusion():
    sc = client.get_or_create_collection("conclusions")
    sc.delete(ids=["sz002594_f39159c0-8192-4386-b268-ea958b0424ae","sz002594_15b22733-eb54-4cd5-8ffc-f87114208677","sz002594_6df9f334-6d46-4b5d-bbd7-30e73cc89805"])
