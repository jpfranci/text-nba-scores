import datetime
import pytz

def format_clock(clock_str):
    if (clock_str == ""):
        return "0:00"
    elif ("." in clock_str):
        return f"{clock_str}s"
    else:
        return clock_str

def to_pacific_date_time(utc_string):
    start_time_utc = datetime.datetime.strptime(utc_string, "%Y-%m-%dT%H:%M:%S.%fz")
    start_time_pacific = start_time_utc.replace(tzinfo=datetime.timezone.utc).astimezone(pytz.timezone('US/Pacific'))
    return str(start_time_pacific.strftime("%a %b %d %I:%M %p"))

def get_today_date():
    today = datetime.datetime.now(pytz.timezone('US/Pacific'))
    return str(today.strftime("%Y%m%d"))