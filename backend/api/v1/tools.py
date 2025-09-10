from fastapi import APIRouter, HTTPException
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()

# naive in-memory tools registry for demo
_tools: Dict[str, Dict] = {
    "search": {"name": "search", "enabled": True, "description": "Vector DB search"},
    "web": {"name": "web", "enabled": False, "description": "Web scraper tool"},
}


class ToolInfo(BaseModel):
    name: str
    enabled: bool
    description: str


@router.get("/", response_model=List[ToolInfo])
def list_tools():
    return list(_tools.values())


@router.post("/{tool_name}/enable")
def enable_tool(tool_name: str):
    if tool_name not in _tools:
        raise HTTPException(status_code=404, detail="tool not found")
    _tools[tool_name]["enabled"] = True
    return {"ok": True, "tool": _tools[tool_name]}


@router.post("/{tool_name}/disable")
def disable_tool(tool_name: str):
    if tool_name not in _tools:
        raise HTTPException(status_code=404, detail="tool not found")
    _tools[tool_name]["enabled"] = False
    return {"ok": True, "tool": _tools[tool_name]}


@router.get("/{tool_name}", response_model=ToolInfo)
def get_tool(tool_name: str):
    if tool_name not in _tools:
        raise HTTPException(status_code=404, detail="tool not found")
    return _tools[tool_name]

