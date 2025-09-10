from pydantic import BaseModel
from typing import List, Optional, Any


class ChatRequest(BaseModel):
    query: str
    tools: Optional[List[str]] = None


class ChatResponse(BaseModel):
    answer: str
    context: Optional[List[Any]] = None

