import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path
from dateutil.parser import parse
from backend.common import logger_client, sconfig
from backend.mcp.servers.prompt.gminiadaptor import GaminiAdaptor

class MarketOpening:

    def __init__(self):
        pass

    def isopen(self,date):
        current_file = Path(__file__)
        parent_dir = current_file.parent.parent / "dep" / "chromedriver.exe"

        chrome_driver_path = str(parent_dir)
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
        url = f"https://www.sse.com.cn/disclosure/dealinstruc/closed/"
        logging.info(f"open url {url}")
        self.driver.get(url)

        content = self.driver.page_source

        llm = GaminiAdaptor()
        prompt = f"今天是{date}，请你参照下面的网页内容，判断今天是开市还是休市？然后输出Y或者N，不要有其他任何的解释\n"
        prompt += content
        r = llm.generate(prompt=prompt, level="high")
        self.driver.quit()
        if r.count("Y") == 1:
            return True
        else:
            return False


if __name__ == "__main__":
    mo = MarketOpening()
    mo.isopen("20251001")