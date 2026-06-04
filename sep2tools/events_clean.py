from datetime import datetime, timedelta
from typing import Any

from .event_overlap import condense_mode_events
from .events_db import get_mode_events
from .times import DEFAULT_TZ, timestamp_local_dt


def get_mode_event_values(
    program: str,
    mode: str,
    tzinfo=DEFAULT_TZ,
    strip_tz: bool = True,
    retro_hours: float = 24.0,
) -> list[dict[str, Any]]:
    events = get_mode_events(program=program, mode=mode)
    data = []
    min_ts = datetime.now(tzinfo) - timedelta(hours=retro_hours)
    if strip_tz:
        min_ts = min_ts.replace(tzinfo=None)
    prev_val = None
    for i, evt in enumerate(condense_mode_events(events)):
        start = evt.intervalStart
        start_dt = timestamp_local_dt(start, tzinfo=tzinfo)
        if strip_tz:
            start_dt = start_dt.replace(tzinfo=None)
        val = evt.controlValue
        multi = evt.controlMultiplier
        if multi != 0:
            val = val * 10**multi
        if i != 0:
            prev_end = timestamp_local_dt(start - 1, tzinfo=tzinfo)
            if strip_tz:
                prev_end = prev_end.replace(tzinfo=None)
            if prev_end > min_ts:
                data.append({"ts": prev_end, "value": prev_val})
        if start_dt > min_ts:
            data.append({"ts": start_dt, "value": val})
        prev_val = val
    return data
