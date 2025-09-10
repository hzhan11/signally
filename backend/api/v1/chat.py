from fastapi import APIRouter, Depends, HTTPException

from models.chat import ChatResponse, ChatRequest
from services import rag

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, chroma=Depends()):
    """Simple chat endpoint: retrieve RAG context and call agent orchestrator."""
    # 1) Retrieve relevant context
    context = await rag.retrieve_context(payload.query, chroma_client=chroma, top_k=3)

    # 2) Build prompt (very simple concatenation for demo)
    prompt = "\n\n".join([c["text"] for c in context]) + "\n\nUser: " + payload.query

    # 3) Call agent orchestrator (could be an AutoGen client / MCP)
    try:
        #agent_response = await agent_orchestrator.call_agent(prompt, tools=payload.tools)
        pass
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return ChatResponse(answer=agent_response, context=context)

