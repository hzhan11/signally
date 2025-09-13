import datetime
import uuid
import os

# 禁用ChromaDB的遥测功能
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'

from chromadb import HttpClient
from chromadb.config import Settings

# 创建客户端时明确禁用遥测
client = HttpClient(
    host="localhost",
    port=8001,
    settings=Settings(anonymized_telemetry=False)
)

def add_info_data():
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

def delete_info_data():
    client.delete_collection("info")

def add_log_connection():
    sc = client.get_collection("log")
    print(sc.count(), sc.name)

def delete_info_log():
    client.delete_collection("log")

add_log_connection()