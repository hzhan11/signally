from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import stocks, chat, ingest, tools
from core.logging import setup_logging
from core.deps import get_httpx_client, close_httpx_client, get_chroma_client
from contextlib import asynccontextmanager
from typing import AsyncGenerator

setup_logging()

@asynccontextmanager  # type: ignore[return-value]
async def lifespan(app) -> AsyncGenerator[None, None]:
    # Startup logic
    get_httpx_client()
    try:
        get_chroma_client()
    except Exception:
        pass
    try:
        yield
    finally:
        await close_httpx_client()

app = FastAPI(title="Signally Gateway", lifespan=lifespan)

# Simple CORS for frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])


@app.get("/health")
def health():
    return {"status": "ok"}
