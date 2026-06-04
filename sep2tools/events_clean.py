from datetime import datetime

from .event_overlap import condense_mode_events
from .events_db import get_mode_events
from .times import timestamp_local_dt


def get_mode_event_values(
    program: str, mode: str
) -> list[tuple[datetime, float | int]]:
    events = get_mode_events(program=program, mode=mode)
    data = []
    for evt in condense_mode_events(events):
        start = evt.intervalStart
        start_dt = timestamp_local_dt(start)
        val = evt.controlValue
        multi = evt.controlMultiplier
        if multi != 0:
            val = val * 10**multi
        data.append((start_dt, val))
    return data
