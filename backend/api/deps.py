import os

from chromadb import HttpClient
from chromadb.config import Settings
from backend.common import sconfig

class ChromaDBSingleton:
    """ChromaDB单例类"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            # 创建客户端时明确禁用遥测
            os.environ['ANONYMIZED_TELEMETRY'] = 'False'
            os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'
            self._client = HttpClient(
                host="localhost",
                port=sconfig.settings.DB_PORT,
                settings=Settings(anonymized_telemetry=False)
            )

    @property
    def client(self):
        """获取ChromaDB客户端"""
        return self._client

    def get_collection(self, name: str, embedding_function=None):
        """获取或创建集合"""
        try:
            return self._client.get_collection(name=name)
        except:
            return self._client.create_collection(
                name=name,
                embedding_function=embedding_function
            )

    def list_collections(self):
        """列出所有集合"""
        return self._client.list_collections()

    def delete_collection(self, name: str):
        """删除集合"""
        return self._client.delete_collection(name=name)