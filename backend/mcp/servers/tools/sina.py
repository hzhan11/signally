import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path
from dateutil.parser import parse
from backend.common import logger_client, sconfig

def find_first_less_than(time_array, target_time):
    for i, time_str in enumerate(time_array):
        if time_str < target_time:  # String comparison works for ISO format
            return i
    return -1

class SinaFinSearcher:

    def __init__(self, stock_id, target_time, fun):

        current_file = Path(__file__)
        parent_dir = current_file.parent.parent / "dep" / "chromedriver.exe"

        chrome_driver_path = str(parent_dir)
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
        url = f"https://gu.qq.com/{stock_id}/gp/news"
        logging.info(f"open url {url}")
        self.driver.get(url)

        self.target_time = target_time.strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"check time after {self.target_time}")
        self.call_back_fun = fun

    def lookahead(self):

        self.whole_urls = []
        self.whole_titles = []
        self.whole_times = []

        logging.info(f"start to look ahead...")

        for i in range(5):
            time.sleep(10)
            links = self.driver.find_elements(
                By.XPATH, '//ul[@data-reactid=".0.0.3.1.0.3.0.1"]//li//a'
            )
            urls = [link.get_attribute("href") for link in links if link.get_attribute("href")]
            titles = [link.get_attribute("title") for link in links if link.get_attribute("title")]

            rights = self.driver.find_elements(
                By.XPATH, '//ul[@data-reactid=".0.0.3.1.0.3.0.1"]//li//span'
            )
            times = [time.text for time in rights]
            index = find_first_less_than(times, self.target_time)

            self.whole_urls.extend(urls[0:index])
            self.whole_titles.extend(titles[0:index])
            self.whole_times.extend(times[0:index])

            if index <= len(times):
                break

        logging.info(f"about {len(self.whole_urls)} related pages found")
        if sconfig.settings.MODE == "debug":
            return 1
        else:
            return len(self.whole_urls)

    async def start(self):
        if sconfig.settings.MODE == "debug":
            length = 1
        else:
            length = len(self.whole_urls)
        for i in range(length):
            logging.info(f"visiting:{self.whole_urls[i]}")
            try:
                self.driver.get(self.whole_urls[i])
                time.sleep(3)
                ele = self.driver.find_element(
                    By.XPATH, '//div[@id="news-text"]'
                )
                md = f"###标题\n{self.whole_titles[i]}\n###链接\n{self.whole_urls[i]}\n###时间\n{self.whole_times[i]}\n###正文\n{ele.text}\n"
                await self.call_back_fun(i+1, len(self.whole_urls), md)
            except Exception as ex:
                logging.error(ex)
            finally:
                continue
        return {"result":"ok"}



if __name__ == "__main__":
    sf = SinaFinSearcher("sz002594", parse("2025-09-15 09:21:24"),None)
    n = sf.lookahead()
    print(n)
    sf.start()