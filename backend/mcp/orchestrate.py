import datetime
import json
import logging
from asyncio import sleep
from zoneinfo import ZoneInfo

from fastmcp import Client

from mcp.shared.context import RequestContext
from fastmcp.client.sampling import SamplingMessage, SamplingParams

import asyncio

from backend.common import logger_client, sconfig
from backend.common.utils import wait_till
from backend.mcp.servers.prompt.gminiadaptor import GaminiAdaptor
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
            logging.info(f"Info Collect Progress: {percentage:.1f}% - {message}")
        else:
            logging.info(f"Info Collect Progress: {progress}")

        if message.startswith("<wait>"):
            return

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

        self.update_message(conversation)

        system_prompt = params.systemPrompt or "You are a helpful assistant."

        response = self.llm_adaptor.generate(system_prompt+"\n"+conversation,level="low")

        tmp = response.replace("```","").replace("json","")
        logging.debug(f"{tmp}")
        return tmp

    async def trader_progress_handler(
        self,
        progress: float,
        total: float | None,
        message: str | None
    ) -> None:
        if total is not None:
            percentage = (progress / total) * 100
            logging.info(f"Trader Progress: {percentage:.1f}% - {message}")
        else:
            logging.info(f"Trader Progress: {progress}")

        if message.startswith("<wait>"):
            return

        mesg = json.loads(message)

        beijing_tz = ZoneInfo('Asia/Shanghai')
        current_beijing_time = datetime.datetime.now(beijing_tz)
        formatted_date = current_beijing_time.strftime("%Y%m%d")

        stock_id = mesg["stock_id"]

        if mesg["t"] == "open_15m_avg" or mesg["t"] == "close":
            url = f"http://localhost:{sconfig.settings.API_PORT}/api/v1/info/add/"
            data = {
                    "type":mesg["t"],
                    "stock_id":stock_id,
                    "formatted_date":formatted_date,
                    "value":mesg["value"],
                    "content":""
                    }
            resp = httpx.post(url, json=data, timeout=10.0)
            logging.info(f"post data {data} with response {resp.content}")
        else:
            pass


    def __init__(self):
        self.llm_adaptor = GaminiAdaptor()
        self.info_col_client = Client(f"http://localhost:{sconfig.settings.INFO_COL_PORT}/mcp", progress_handler=self.info_col_progress_handler)
        self.sign_pred_client = Client(f"http://localhost:{sconfig.settings.SIGN_PRE_PORT}/mcp",sampling_handler=self.sign_pred_sampling_handler)
        self.trader_client = Client(f"http://localhost:{sconfig.settings.TRADER_PORT}/mcp", progress_handler=self.trader_progress_handler)
        self.memory = []
        # cache last sent values to avoid spamming API
        self._last_status: str | None = None
        self._last_message: str | None = None

    # -----------------------------
    # 更新系统状态（去重 + 简单错误处理）
    # -----------------------------
    def update_status(self, status: str):
        if not isinstance(status, str):
            status = str(status)
        if status == self._last_status:
            return  # no change
        url = f"http://localhost:{sconfig.settings.API_PORT}/api/v1/highlights/system_status"
        try:
            resp = httpx.post(url, json={"value": status}, timeout=5.0)
            if resp.status_code >= 400:
                logging.warning(f"update_status failed {resp.status_code}: {resp.text}")
            else:
                self._last_status = status
                logging.info(f"[orchestrate] system_status -> {status}")
        except Exception as e:
            logging.error(f"update_status exception: {e}")

    # -----------------------------
    # 更新最后消息（去重长度截断 + 简单错误处理）
    # -----------------------------
    def update_message(self, msg: str):
        if msg is None:
            return
        if not isinstance(msg, str):
            msg = str(msg)
        # 适度截断，避免超长（前端卡片显示）
        MAX_LEN = 100
        if len(msg) > MAX_LEN:
            msg_to_send = msg[:MAX_LEN] + '…'
        else:
            msg_to_send = msg
        if msg_to_send == self._last_message:
            return
        url = f"http://localhost:{sconfig.settings.API_PORT}/api/v1/highlights/last_message"
        try:
            resp = httpx.post(url, json={"value": msg_to_send}, timeout=5.0)
            if resp.status_code >= 400:
                logging.warning(f"update_message failed {resp.status_code}: {resp.text}")
            else:
                self._last_message = msg_to_send
                logging.debug(f"[orchestrate] last_message updated length={len(msg_to_send)}")
        except Exception as e:
            logging.error(f"update_message exception: {e}")

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
            response = self.llm_adaptor.generate(system_prompt+"\n"+json_string, level="high")
            tmp = response.replace("```", "").replace("json", "")
            logging.info(f"final conclusion is {tmp}")
            self.conclusion(stock, json.loads(tmp))

    def update_cache(self):
        url = f"http://localhost:{sconfig.settings.API_PORT}/api/v1/highlights/generate"
        resp = httpx.get(url, timeout=30.0)
        logging.info(f"{resp}")

    async def go_with_info_collector(self, stock):
        await wait_till("08:45:00", self.info_col_progress_handler)
        logging.info("start to collect news and info...")
        async with self.info_col_client:
            result = await self.info_col_client.call_tool("search", {"src": settings.INFO_SRC_YHF, "stock": stock})
            result = await self.info_col_client.call_tool("search", {"src":settings.INFO_SRC_AKS,"stock": stock})
            result = await self.info_col_client.call_tool("search", {"src": settings.INFO_SRC_CLS, "stock": stock})
            result = await self.info_col_client.call_tool("search", {"src":settings.INFO_SRC_SINA,"stock": stock})
        logging.info("start to make the finial decision...")
        self.final(stock)

    async def run(self):

        while True:

            try:
                async with self.info_col_client:
                    while True:
                        self.update_status("判断开市情况")
                        result = await self.info_col_client.call_tool("opening")
                        is_open = result.data["result"]
                        if is_open:
                            break
                        else:
                            self.update_status("休市")
                            logging.info("today is close, wait for 24hrs to check again...")
                            await sleep(3600 * 24)

                self.update_status("查询金融新闻和股票交易数据")
                for stock in self.get_stock_list():
                    if "status" in stock["metadata"].keys() and stock["metadata"]["status"] == "active":
                        await self.go_with_info_collector(stock)

                self.update_status("股票交易信息监控")
                for stock in self.get_stock_list():
                    if "status" in stock["metadata"].keys() and stock["metadata"]["status"] == "active":
                        async with self.trader_client:
                            result = await self.trader_client.call_tool("trade",{"stock": stock})
                self.update_cache()
            except Exception as ex:
                logging.error(str(ex))

            self.update_status("等待盘后整理")
            await wait_till("23:59:59", self.info_col_progress_handler)
            await sleep(120)

if __name__ == "__main__":
    logger_client.init("orchestrate")
    async def main() -> None:
        await sleep(15)
        await Orchestrate().run()
    asyncio.run(main())