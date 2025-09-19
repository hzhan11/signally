# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.deps import ChromaDBSingleton
from backend.api.v1 import stocks, info, conclusions
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uvicorn

from backend.common import logger_client, sconfig

# -----------------------------
# Lifespan with logging init
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 初始化 logger
    logger_client.init("api")
    ChromaDBSingleton()
    yield  # 必须 yield 才能让 FastAPI 启动

# -----------------------------
# 创建 FastAPI app
# -----------------------------
app = FastAPI(title="Signally Gateway", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])
app.include_router(info.router, prefix="/api/v1/info", tags=["info"])
app.include_router(conclusions.router, prefix="/api/v1/conclusions", tags=["conclusions"])

# health check
@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# 启动 FastAPI (uvicorn)
# -----------------------------
if __name__ == "__main__":
    # 可以直接用 Python 启动： python main.py
    uvicorn.run(
        "api_main:app",  # 模块名:对象名
        host="127.0.0.1",
        port=sconfig.settings.API_PORT,
        log_level="info",
        reload=True  # 开发模式自动热重载，可选
    )
