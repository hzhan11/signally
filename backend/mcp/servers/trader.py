import json
import logging
from typing import Dict, Any
from fastmcp import FastMCP, Context
import akshare as ak
import pytz
import pandas as pd
from datetime import datetime
from backend.common.utils import bj_time, wait_till, remove_letter_prefix
from backend.common import logger_client, sconfig

mcp = FastMCP("Trader")

def print_and_average_open_between_bj(df, start_time="09:30:00", end_time="09:45:00"):
    """
    打印当天北京时间 09:30-09:45 的所有数据，并返回 open 平均值
    """
    # 确保 'day' 列是 datetime 类型
    df['day'] = pd.to_datetime(df['day'])

    # 将 open 列转换为数值类型
    df['open'] = pd.to_numeric(df['open'], errors='coerce')

    # 获取今天的北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    today_bj = datetime.now(beijing_tz).date()

    # 筛选当天的数据
    df['date'] = df['day'].dt.date
    df['time'] = df['day'].dt.time

    start = pd.to_datetime(start_time).time()
    end = pd.to_datetime(end_time).time()

    mask = (df['date'] == today_bj) & df['time'].between(start, end)
    filtered_df = df[mask]

    if filtered_df.empty:
        logging.info(f"当天 {start_time}-{end_time} 没有数据")
        return -1.0

    # 打印筛选后的数据
    logging.info(f"当天 {start_time}-{end_time} 的所有数据:")
    logging.info(str(filtered_df))

    # 计算 open 列平均值
    avg_open = filtered_df['open'].mean()
    logging.info(f"平均 open 值: {avg_open}")
    return avg_open


def print_and_close(minute_df):
    """
    获取北京时间当天的收盘价格

    Parameters:
    minute_df (pd.DataFrame): 包含交易数据的DataFrame，必须包含'day'和'close'列

    Returns:
    float: 当天的收盘价格
    """

    # 确保day列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(minute_df['day']):
        minute_df['day'] = pd.to_datetime(minute_df['day'])

    # 获取北京时区
    beijing_tz = pytz.timezone('Asia/Shanghai')

    # 获取当前北京时间的日期
    current_beijing_time = datetime.now(beijing_tz)
    current_date = current_beijing_time.date()

    # 筛选当天的数据
    today_data = minute_df[minute_df['day'].dt.date == current_date]

    if today_data.empty:
        print(f"没有找到{current_date}的交易数据")
        return -1

    # 获取当天最后一条记录的收盘价（即当天收盘价）
    closing_price = today_data.iloc[-1]['close']

    print(f"北京时间 {current_date} 的收盘价格: {closing_price}")

    return closing_price

@mcp.tool
async def trade(stock: Dict[str, Any], ctx: Context = None) -> dict:
    symbol = stock["id"]
    logging.info(stock)

    await wait_till("09:45:00", ctx.report_progress)
    minute_df = ak.stock_zh_a_minute(symbol=symbol, period="1", adjust="")  # adjust 可选: "" / "qfq" / "hfq"
    logging.info(str(minute_df))
    avg = print_and_average_open_between_bj(minute_df, "09:30:00", "09:45:00")
    msg_json = {"t":"open_15m_avg","value":avg,"stock_id":stock["id"]}
    await ctx.report_progress(1,2, json.dumps(msg_json))

    await wait_till("16:10:00", ctx.report_progress)
    minute_df = ak.stock_zh_a_minute(symbol=symbol, period="1", adjust="")  # adjust 可选: "" / "qfq" / "hfq"
    close = print_and_close(minute_df)
    msg_json = {"t": "close", "value": close, "stock_id": stock["id"]}
    await ctx.report_progress(2, 2, json.dumps(msg_json))
    return {"result": "ok"}

logger_client.init("Trader")
mcp.run(transport="http", host="127.0.0.1", port=sconfig.settings.TRADER_PORT)