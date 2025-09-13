from datetime import datetime
from dateutil.parser import parse
from fastmcp import FastMCP, Context

from sina.newscollector import SinaFinSearcher

mcp = FastMCP("InfoCollector")

class InfoSrc:
    sina = "新浪证券"

@mcp.tool
async def search(
    source: str = InfoSrc.sina,
    targettime: datetime = None,
    target: str = "",
    maxcount: int = 100,
    ctx: Context = None
) -> dict:

    agent = None
    if source == InfoSrc.sina:
        agent = SinaFinSearcher("sz002594", parse("2025-09-12 23:28:00"), ctx.report_progress)

    n = agent.lookahead()
    await agent.start()
    return {"processed": n, "result": "ok"}

mcp.run(transport="http", host="127.0.0.1", port=9000)