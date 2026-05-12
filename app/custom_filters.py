
from datetime import datetime
import pytz

def format_datetime_gmt7(value):
    if value is None:
        return ""
    utc_tz = pytz.utc
    gmt7_tz = pytz.timezone('Asia/Bangkok')
    utc_dt = value.replace(tzinfo=utc_tz)
    gmt7_dt = utc_dt.astimezone(gmt7_tz)
    return gmt7_dt.strftime('%d-%m-%Y %H:%M:%S')