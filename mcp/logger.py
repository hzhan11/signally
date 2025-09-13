import logging
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


class ChromaLogHandler(logging.Handler):
    def __init__(self, client: HttpClient, collection_name: str = "log", level=logging.NOTSET):
        super().__init__(level)
        self.client = client
        self.collection_name = collection_name
        self.sc = self.client.get_or_create_collection(self.collection_name)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            ts = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            mesg = self.format(record)
            py = record.pathname or record.module or ""
            self.sc.upsert(
                ids=[str(uuid.uuid4())],
                documents=[mesg],
                metadatas=[{"time": ts, "mesg": mesg, "py": py}],
            )
        except Exception:
            # 静默处理所有错误
            pass


def setup_logging(level: int = logging.INFO) -> None:
    # 禁用所有可能的第三方日志
    third_party_loggers = [
        'chromadb', 'httpx', 'urllib3', 'requests',
        'httpcore', 'posthog', 'backoff', 'opentelemetry'
    ]
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)  # 只显示错误

    # 只给你的应用logger添加ChromaLogHandler
    app_logger = logging.getLogger("signally")
    app_logger.setLevel(level)
    app_logger.handlers.clear()  # 清除现有处理器

    # 添加ChromaDB处理器
    chroma_handler = ChromaLogHandler(client)
    chroma_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    chroma_handler.setFormatter(chroma_formatter)
    app_logger.addHandler(chroma_handler)

    # 控制台日志
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    app_logger.addHandler(console)

    # 防止日志传播到root logger
    app_logger.propagate = False

logger = logging.getLogger("signally")