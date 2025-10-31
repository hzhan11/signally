import logging
from pathlib import Path
from typing import Dict, Any

from fastmcp import FastMCP, Context
import json

from backend.common import logger_client, sconfig
from backend.common.utils import bj_time

mcp = FastMCP("SignalPredictor")

p1 = Path(__file__).parent / "prompt" / "signal_predictor_news.prompt"
prompt_template = open(p1,"r",encoding="utf-8").read()

@mcp.tool
async def predict(news: str, stock:Dict[str, Any], ctx: Context) -> dict:

    system_prompt = prompt_template.replace("[TIME]",str(bj_time(offset=0)))
    system_prompt = system_prompt.replace("[STOCK]", stock["metadata"]["name"])

    response = await ctx.sample(
        messages=news,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=30
    )

    return json.loads(response.text)

logger_client.init("signalpredictor")
mcp.run(transport="http", host="127.0.0.1", port=sconfig.settings.SIGN_PRE_PORT)