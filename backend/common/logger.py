import logging
import datetime
import uuid

from chromadb import HttpClient
client = HttpClient(host="localhost", port=8001)

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
            self.handleError(record)


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    # remove duplicate handlers of same type
    if not any(isinstance(h, ChromaLogHandler) for h in root.handlers):
        chroma_handler = ChromaLogHandler(client)
        chroma_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        chroma_handler.setFormatter(chroma_formatter)
        root.addHandler(chroma_handler)

    # also keep console logging
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        root.addHandler(console)


logger = logging.getLogger("signally")

