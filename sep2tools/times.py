from datetime import datetime, timedelta, timezone

from dateutil import tz

LOCAL_TZ = tz.tzlocal()


def current_timestamp() -> int:
    now_utc = datetime.now(timezone.utc).timestamp()
    return int(now_utc)


def next_interval(interval_min: int = 5) -> int:
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    now = now + timedelta(minutes=1)  # Add a buffer
    delta = timedelta(minutes=(interval_min - now.minute % interval_min))
    next_dt = now + delta
    return next_dt.timestamp()


def timestamp_local_dt(start: int) -> datetime:
    utc_dt = datetime.fromtimestamp(start, tz=timezone.utc)
    return utc_dt.astimezone(LOCAL_TZ)


def event_time_range(start: int, duration: int) -> tuple[datetime, datetime]:
    start_dt = timestamp_local_dt(start)
    end_dt = start_dt + timedelta(seconds=duration)
    return start_dt, end_dt
