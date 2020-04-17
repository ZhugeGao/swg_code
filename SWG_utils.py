"""helper methods for the swg project data processing"""
import datetime


def timestamp_convert(ts):
    ts_list = str(ts).split('.')
    remaining_seconds = int(ts_list[0])
    ms = int(ts_list[1])
    hour = 0
    minute = 0
    if remaining_seconds >= 3600:
        hour = remaining_seconds // 3600
        remaining_seconds = remaining_seconds - (hour * 3600)
    if remaining_seconds >= 60:
        minute = remaining_seconds // 60
        remaining_seconds = remaining_seconds - (minute * 60)
    second = remaining_seconds
    # could try gmtime or other python time function
    timestamp = datetime.time(hour, minute, second, ms).strftime('%H:%M:%S.%f')
    return timestamp