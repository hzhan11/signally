import asyncio
import logging

import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from dateutil.parser import parse
from backend.common import logger_client, sconfig

def find_first_less_than(time_array, target_time):
    for i, time_str in enumerate(time_array):
        if time_str < target_time:  # String comparison works for ISO format
            return i
    return -1

class ClsTelSearcher:

    def __init__(self, fun):

        current_file = Path(__file__)
        parent_dir = current_file.parent.parent / "dep" / "chromedriver.exe"

        chrome_driver_path = str(parent_dir)
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)

        self.driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
            "timezoneId": "Asia/Shanghai"
        })

        self.call_back_fun = fun
        self.eles = []

    def lookahead(self):

        self.driver.get("https://www.cls.cn/telegraph")
        time.sleep(5)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        for i in range(5):
            try:
                element = self.driver.find_element(By.XPATH, "//*[text()='加载更多']")
                element.click()
                time.sleep(5)
            except NoSuchElementException as ex:
                pass
            finally:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)

        self.eles = self.driver.find_elements(
            By.XPATH, "//span[@class='c-34304b']/div"
        )

        self.times = self.driver.find_elements(
            By.XPATH, "//span[@class='f-l l-h-136363 f-w-b c-de0422 m-r-10 telegraph-time-box']"
        )

        logging.info(f"about {len(self.eles)} related news found")
        if sconfig.settings.MODE == "debug":
            return 1
        else:
            return len(self.eles)

    async def start(self):
        if sconfig.settings.MODE == "debug":
            length = 1
        else:
            length = len(self.eles)
        batch = ""

        try:
            for i in range(length):
                try:
                    t = self.times[i].text
                    content = self.eles[i].text
                    content = content.replace("日电",f"日{t}电")
                    batch += f"###快讯\n{content}\n\n"
                    if i % 10 == 9 or i == length-1:
                        await self.call_back_fun(i+1, length, batch)
                        batch = ""
                except Exception as ex:
                    logging.error(ex)
                finally:
                    continue
        finally:
            self.driver.quit()
        return {"result":"ok"}

async def call_back(index, total, mesg):
    print(index,total)
    print(mesg)

async def main():
    sf = ClsTelSearcher(call_back)
    n = sf.lookahead()
    print(n)
    await sf.start()

if __name__ == "__main__":
    asyncio.run(main())