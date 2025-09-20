#TODO 要控制调用API的速率，不然在这里就会挂掉，想想办法

import logging
from pathlib import Path
from fastmcp import FastMCP, Context
import json

from backend.common import logger_client, sconfig

mcp = FastMCP("SignalPredictor")

p1 = Path(__file__).parent / "prompt" / "signal_predictor_news.prompt"
prompt_template = open(p1,"r",encoding="utf-8").read()

@mcp.tool
async def predict(news: str, ctx: Context) -> dict:

    #system_prompt = prompt_template.replace("{time}","2025/09/14 14:20:30")
    #system_prompt = system_prompt.replace("{left}","30分钟")
    #system_prompt = system_prompt.replace("{stock}", "比亚迪")
    system_prompt = prompt_template

    response = await ctx.sample(
        messages=news,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=30
    )

    return json.loads(response.text)

logger_client.init("signalpredictor")
mcp.run(transport="http", host="127.0.0.1", port=sconfig.settings.SIGN_PRE_PORT)