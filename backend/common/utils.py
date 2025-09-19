from datetime import datetime, timedelta
import pytz

def bj_time(offset=24):
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = datetime.now(beijing_tz)
    if offset > 0:
        beijing_time = beijing_time - timedelta(hours=offset)
    return beijing_time