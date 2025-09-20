import datetime
import json
import logging
from asyncio import sleep
from zoneinfo import ZoneInfo

from fastmcp import Client
from google.genai import types
from mcp.shared.context import RequestContext
from fastmcp.client.sampling import SamplingMessage, SamplingParams

import asyncio
from google import genai

from backend.common import logger_client, sconfig

import httpx

from backend.common.sconfig import settings


class Orchestrate:

    async def info_col_progress_handler(
        self,
        progress: float,
        total: float | None,
        message: str | None
    ) -> None:
        if total is not None:
            percentage = (progress / total) * 100
            logging.info(f"Info Collect Progress: {percentage:.1f}% \n")
        else:
            logging.info(f"Info Collect Progress: {progress} \n")

        async with self.sign_pred_client:
            result = await self.sign_pred_client.call_tool("predict", {"news": message})
            logging.info(f"{result}")
            self.memory.append(result.data)

    async def sign_pred_sampling_handler(
        self,
        messages: list[SamplingMessage],
        params: SamplingParams,
        context: RequestContext
    ) -> str:
        conversation = ""
        for message in messages:
            conversation += message.content.text + "\n"

        system_prompt = params.systemPrompt or "You are a helpful assistant."

        response = self.google_client.models.generate_content(
            model="gemma-3-27b-it",
            contents=system_prompt+"\n"+conversation
        )
        tmp = response.text.replace("```","").replace("json","")
        logging.debug(f"{tmp}")
        return tmp

    def __init__(self):
        self.google_client = genai.Client(api_key="AIzaSyAf8NARQmskJOPz4QJtGBNZbE1lS3H-CV8")
        self.info_col_client = Client(f"http://localhost:{sconfig.settings.INFO_COL_PORT}/mcp", progress_handler=self.info_col_progress_handler)
        self.sign_pred_client = Client(f"http://localhost:{sconfig.settings.SIGN_PRE_PORT}/mcp",sampling_handler=self.sign_pred_sampling_handler)
        self.memory = []

    def get_stock_list(self):
        response = httpx.get(f"http://localhost:{sconfig.settings.API_PORT}/api/v1/stocks/list")
        logging.info(response.status_code)
        logging.info(response.json())
        return response.json()

    def conclusion(self, stock, item):
        url = f"http://localhost:{sconfig.settings.API_PORT}/api/v1/conclusions/add"
        beijing_tz = ZoneInfo('Asia/Shanghai')
        current_beijing_time = datetime.datetime.now(beijing_tz)
        formatted_date = current_beijing_time.strftime("%Y%m%d")
        data = {
            "stock": stock["id"],
            "datetime": formatted_date,
            "prediction": item["趋势"],
            "confidence": item["置信度"],
            "document": item["理由"]
        }
        logging.info(str(data))
        resp = httpx.post(url, json=data, timeout=10.0)
        logging.info(f"{resp}")

    def final(self, stock):
        json_string = json.dumps(self.memory, ensure_ascii=False, indent=2)
        with open("./servers/prompt/final.prompt","r",encoding="utf-8") as f:
            system_prompt = f.read()
            try:
                response = self.google_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=system_prompt+"\n"+json_string,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=-1)
                    ),
                )
            except:
                response = self.google_client.models.generate_content(
                    model="gemma-3-27b-it",
                    contents=system_prompt+"\n"+json_string,
                )
            tmp = response.text.replace("```", "").replace("json", "")
            logging.info(f"final conclusion is {tmp}")
            self.conclusion(stock, json.loads(tmp))

    async def go_with_info_collector(self, stock):
        logging.info("start to collect news and info...")
        async with self.info_col_client:
            result = await self.info_col_client.call_tool("search", {"src": settings.INFO_SRC_YHF, "stock": stock})
            result = await self.info_col_client.call_tool("search", {"src":settings.INFO_SRC_AKS,"stock": stock})
            result = await self.info_col_client.call_tool("search", {"src": settings.INFO_SRC_CLS, "stock": stock})
            result = await self.info_col_client.call_tool("search", {"src":settings.INFO_SRC_SINA,"stock": stock})
        logging.info("start to make the finial decision...")
        self.final(stock)

    async def run(self):
        for stock in self.get_stock_list():
            await self.go_with_info_collector(stock)

if __name__ == "__main__":
    logger_client.init("orchestrate")
    async def main() -> None:
        await sleep(15)
        await Orchestrate().run()
    asyncio.run(main())