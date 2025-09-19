import uvicorn
import logging
import os
import chromadb
from pathlib import Path
from backend.common import logger_client, sconfig
from chromadb.config import Settings

def main():
    logger_client.init("db")
    port = sconfig.settings.DB_PORT
    os.environ["IS_PERSISTENT"] = "TRUE"  # Ensure persistence is enabled
    logging.info(f"Starting ChromaDB server on 0.0.0.0:{port}")
    #logging.info(f"Data directory: {db_dir}")

    uvicorn.run(
        "chromadb.app:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()