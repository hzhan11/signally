import asyncio
import logging
import re
from datetime import datetime, timedelta
import pytz
import time

def remove_letter_prefix(s):
    return re.sub(r'^[A-Za-z]+', '', s)

def bj_time(offset=24):
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = datetime.now(beijing_tz)
    if offset > 0:
        beijing_time = beijing_time - timedelta(hours=offset)
    return beijing_time

async def wait_till(target_time_str, progress_call_back):
    start = bj_time(0)

    target_time_today = datetime.strptime(target_time_str, "%H:%M:%S").time()
    target_datetime = start.replace(hour=target_time_today.hour,
                                  minute=target_time_today.minute,
                                  second=target_time_today.second,
                                  microsecond=0)

    while True:
        now = bj_time(0)

        if now >= target_datetime:
            logging.info(f"当前时间 {now} 已到达或超过目标时间 {target_time_str}")
            break
        else:
            progress = 10000 - int((target_datetime - now).total_seconds() * 10000 / (target_datetime - start).total_seconds())
            await progress_call_back(progress, 10000, f"<wait> now is {now.strftime('%H:%M:%S')} and waiting for {target_time_str}")
            await asyncio.sleep(60)

async def ppp(progress,total,m):
    if total is not None:
        percentage = (progress / total) * 100
        print(f"Trader Progress: {percentage:.1f}% \n")
    else:
        print(f"Trader Progress: {progress} \n")

if __name__ == "__main__":
    print("等待至09:59:00...")
    asyncio.run(wait_till("09:59:00", ppp))
    print("时间到，继续执行后续代码")