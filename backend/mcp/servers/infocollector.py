from typing import Dict, Any


from fastmcp import FastMCP, Context

from backend.common.sconfig import settings
from backend.common.utils import bj_time
from backend.mcp.servers.tools.aksapi import AKSApi
from backend.mcp.servers.tools.marketopen import MarketOpening
from backend.mcp.servers.tools.sina import SinaFinSearcher
from backend.mcp.servers.tools.clstel import ClsTelSearcher
from backend.mcp.servers.tools.yahoof import YahooFAPI
from backend.common import logger_client, sconfig


mcp = FastMCP("InfoCollector")

@mcp.tool
async def search(
    src:str,
    stock:Dict[str, Any],
    ctx: Context = None
) -> dict:

    agent = None
    if settings.INFO_SRC_SINA == src:
        agent = SinaFinSearcher(stock["id"], bj_time(offset=12), ctx.report_progress)
    elif settings.INFO_SRC_AKS == src:
        agent = AKSApi(stock["id"], ctx.report_progress)
    elif settings.INFO_SRC_YHF == src:
        agent = YahooFAPI(stock["metadata"]["usid"], ctx.report_progress)
    elif settings.INFO_SRC_CLS == src:
        agent = ClsTelSearcher(ctx.report_progress)
    else:
        pass

    n = agent.lookahead()
    await agent.start()
    return {"processed": n, "result": "ok"}

@mcp.tool
async def opening(

) -> dict:
    mo = MarketOpening()
    r = mo.isopen(bj_time(0).strftime("%Y-%m-%d"))
    return {"result": r}

logger_client.init("InfoCollector")
mcp.run(transport="http", host="127.0.0.1", port=sconfig.settings.INFO_COL_PORT)