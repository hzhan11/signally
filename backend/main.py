from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1 import stocks,info
from backend.common.logger import setup_logging
from backend.common.deps import get_chroma_client
from contextlib import asynccontextmanager
from typing import AsyncGenerator

setup_logging()

@asynccontextmanager  # type: ignore[return-value]
async def lifespan(app) -> AsyncGenerator[None, None]:
    try:
        get_chroma_client()
    except Exception:
        pass
    try:
        yield
    finally:
        pass

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
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["stocks"])
app.include_router(info.router, prefix="/api/v1/info", tags=["info"])


@app.get("/health")
def health():
    return {"status": "ok"}
