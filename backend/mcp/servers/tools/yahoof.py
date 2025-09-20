import yfinance as yf

import asyncio
import datetime
import pandas as pd

class YahooFAPI:

    def __init__(self, stock_id, call_back_f):
        self.call_back_fun = call_back_f
        self.stock_id = stock_id
        self.total_functions = 13

    def lookahead(self):
        return self.total_functions

    async def start(self):

        pd.set_option('display.max_columns', None)  # 显示所有列
        pd.set_option('display.width', None)  # 不限制显示宽度

        content = ""

        stock_symbol = self.stock_id

        stock = yf.Ticker(stock_symbol)

        call_back_fun = self.call_back_fun
        total_functions = self.total_functions
        stop_time = "美国东部时间" + str(datetime.datetime.now())

        # ===== 基本信息 =====
        df_info = stock.info
        current = f"### 个股在{stop_time}的基本信息：\n{str(df_info)}\n"
        await call_back_fun(1, total_functions, current)
        content += current

        # ===== 最近5天日线行情 =====
        df_hist = stock.history(period="5d")
        current = f"### 个股在{stop_time}的最近5天日线行情：\n{str(df_hist)}\n"
        await call_back_fun(2, total_functions, current)
        content += current

        # ===== 财务报表 =====
        try:
            df_financials = stock.financials
            current = f"### 个股在{stop_time}的年度财务报表：\n{str(df_financials)}\n"
            await call_back_fun(3, total_functions, current)
            content += current

            df_quarterly_fin = stock.quarterly_financials
            current = f"### 个股在{stop_time}的季度财务报表：\n{str(df_quarterly_fin)}\n"
            await call_back_fun(4, total_functions, current)
            content += current
        except:
            pass

        # ===== 资产负债表 =====
        try:
            df_bs = stock.balance_sheet
            current = f"### 个股在{stop_time}的年度资产负债表：\n{str(df_bs)}\n"
            await call_back_fun(5, total_functions, current)
            content += current

            df_quarterly_bs = stock.quarterly_balance_sheet
            current = f"### 个股在{stop_time}的季度资产负债表：\n{str(df_quarterly_bs)}\n"
            await call_back_fun(6, total_functions, current)
            content += current
        except:
            pass

        # ===== 现金流量表 =====
        try:
            df_cf = stock.cashflow
            current = f"### 个股在{stop_time}的年度现金流量表：\n{str(df_cf)}\n"
            await call_back_fun(7, total_functions, current)
            content += current

            df_quarterly_cf = stock.quarterly_cashflow
            current = f"### 个股在{stop_time}的季度现金流量表：\n{str(df_quarterly_cf)}\n"
            await call_back_fun(8, total_functions, current)
            content += current
        except:
            pass

        # ===== 股息与拆分 =====
        try:
            df_div = stock.dividends
            current = f"### 个股在{stop_time}的股息记录：\n{str(df_div)}\n"
            await call_back_fun(9, total_functions, current)
            content += current

            df_splits = stock.splits
            current = f"### 个股在{stop_time}的拆分记录：\n{str(df_splits)}\n"
            await call_back_fun(10, total_functions, current)
            content += current
        except:
            pass

        # ===== 分析师评级 =====
        try:
            df_rec = stock.recommendations
            current = f"### 个股在{stop_time}的分析师评级：\n{str(df_rec)}\n"
            await call_back_fun(11, total_functions, current)
            content += current
        except:
            pass

        # ===== 机构持股 =====
        try:
            df_major = stock.major_holders
            current = f"### 个股在{stop_time}的主要股东：\n{str(df_major)}\n"
            await call_back_fun(12, total_functions, current)
            content += current

            df_insti = stock.institutional_holders
            current = f"### 个股在{stop_time}的机构持股：\n{str(df_insti)}\n"
            await call_back_fun(13, total_functions, current)
            content += current
        except:
            pass

        return {"result":content}

async def call_back(cu,to,me):
    print(me)

async def main():
    yfapi = YahooFAPI("BYDDY", call_back)
    print(yfapi.lookahead())
    res = await yfapi.start()

if __name__ == "__main__":
    asyncio.run(main())