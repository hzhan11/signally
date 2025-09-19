import asyncio

from dateutil.parser import parse

import akshare as ak
from backend.common.utils import bj_time
import re
import pandas as pd

def remove_letter_prefix(s):
    return re.sub(r'^[A-Za-z]+', '', s)

class AKSApi:
    def __init__(self, stock_id, call_back):
        self.call_back_fun = call_back
        self.stock_id = stock_id
        self.stock_symbol = remove_letter_prefix(stock_id)
        self.stop_time = bj_time(offset=0)
        self.start_time_24hr = bj_time(offset=24)
        self.start_time_7days = bj_time(offset=24*7)
        self.total_functions = 9

    def lookahead(self):
        return self.total_functions

    async def start(self):

        pd.set_option('display.max_columns', None)  # 显示所有列
        pd.set_option('display.width', None)  # 不限制显示宽度

        content = ""

        df = ak.stock_individual_info_em(symbol=self.stock_symbol)
        current = f"###个股在{self.stop_time}的基本信息：\n{str(df)}\n"
        await self.call_back_fun(1, self.total_functions, current)
        content+=current

        df = ak.stock_hot_rank_latest_em(symbol=self.stock_id)
        current = f"###个股在{self.stop_time}的人气榜-最新排名：\n{str(df)}\n"
        await self.call_back_fun(2, self.total_functions, current)
        content += current

        df = ak.stock_hot_keyword_em(symbol=self.stock_id)
        current = f"###个股在{self.stop_time}个股人气榜-热门关键词：\n{str(df)}\n"
        await self.call_back_fun(3, self.total_functions, current)
        content += current
        
        df = ak.stock_value_em(symbol=self.stock_symbol)
        df = df.tail(10)
        current = f"###个股在{self.stop_time}个股估值十日变化：\n{str(df)}\n"
        await self.call_back_fun(4, self.total_functions, current)
        content += current
        
        df = ak.stock_zygc_em(symbol=self.stock_id)
        df = df[0:7]
        current = f"###个股在{self.stop_time}主营构成：\n{str(df)}\n"
        await self.call_back_fun(5, self.total_functions, current)
        content += current
        
        df = ak.stock_zh_a_hist(symbol=self.stock_symbol,
             period="daily",
             start_date=self.start_time_7days.strftime("%Y%m%d"),
             end_date=self.stop_time.strftime("%Y%m%d"), adjust="")
        current = f"###个股在{self.stop_time}过去7日的历史行情数据：\n{str(df)}\n"
        await self.call_back_fun(6, self.total_functions, current)
        content += current        

        df = ak.stock_financial_debt_ths(symbol=self.stock_symbol, indicator="按报告期")
        df = df[0:1]
        current = f"###个股在{self.stop_time}最近一次资产负债表：\n{str(df)}\n"
        await self.call_back_fun(7, self.total_functions, current)
        content += current

        df = ak.stock_financial_benefit_ths(symbol=self.stock_symbol, indicator="按报告期")
        df = df[0:1]
        current = f"###个股在{self.stop_time}最近一次利润表：\n{str(df)}\n"
        await self.call_back_fun(8, self.total_functions, current)
        content += current
        
        df = ak.stock_financial_cash_ths(symbol=self.stock_symbol, indicator="按报告期")
        df = df[0:1]
        current = f"###个股在{self.stop_time}最近一次现金流量表：\n{str(df)}\n"
        await self.call_back_fun(9, self.total_functions, current)
        content += current

        return {"result":content}

async def call_back(cu,to,me):
    print(me)

async def main():
    aksapi = AKSApi("sz002594", call_back)
    print(aksapi.lookahead())
    res = await aksapi.start()
    print(res)

if __name__ == "__main__":
    asyncio.run(main())