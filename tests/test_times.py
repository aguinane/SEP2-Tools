from datetime import date

from sep2tools.times import (
    current_timestamp,
    day_time_range,
    event_days,
    timestamp_local_dt,
)


def test_current_timestamp():
    now = current_timestamp()
    assert isinstance(now, int)
    assert now > 1780000000


def test_datetime_conversion():
    ts = 1780000000
    dt = timestamp_local_dt(ts)
    assert dt.year == 2026
    assert dt.month == 5
    assert dt.day == 29


def test_event_days():
    ts = 1780000000
    days = event_days(ts, end=ts + 1000)
    assert len(days) == 3
    assert days[0] == date(2026, 5, 29)


def test_day_range():
    day = date(2026, 5, 29)
    start, end = day_time_range(day)
    assert start == 1779976800
    assert end == 1780063200
