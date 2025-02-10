from datetime import date
from typing import Any

from .eventsdb import get_day_mode_events, get_mode_events, get_modes
from .times import timestamp_local_dt


def get_modes_data(der: str, day: date | None = None) -> list[dict[str, Any]]:
    data = []
    for mode in get_modes(der):
        if day:
            mode_events = get_day_mode_events(der, mode, day)
        else:
            mode_events = get_mode_events(der, mode)
        for evt in mode_events:
            start = timestamp_local_dt(evt.start).replace(tzinfo=None)
            item = {"mode": mode, "time": start, "value": evt.value}
            data.append(item)
            end = timestamp_local_dt(evt.end).replace(tzinfo=None)
            item = {"mode": mode, "time": end, "value": evt.value}
            data.append(item)
    return data


DEFAULT_DIST_BREAKS = (1500, 5000, 10000)


def get_mode_day_distribution(
    der: str, mode: str, day: date, breaks: tuple[int] = DEFAULT_DIST_BREAKS
):
    mode_events = get_day_mode_events(der, mode, day)
    max_value = max([x.value for x in mode_events])
    min_value = min([x.value for x in mode_events])
    num_seconds = 0

    for evt in mode_events:
        duration = evt.end - evt.start
        num_seconds += duration

    if num_seconds != 86400:
        msg = f"Incomplete events for {der} {mode} {day}"
        raise ValueError(msg)

    output = {
        "der": der,
        "mode": mode,
        "day": str(day),
        "min_value": min_value,
        "max_value": max_value,
    }

    # Determine time at maximum
    output["s_at_max"] = sum(
        [evt.end - evt.start for evt in mode_events if evt.value == max_value]
    )

    # Determine time at break points
    breaks = sorted(tuple(breaks), reverse=True)
    for break_val in breaks:
        output[f"s_at_or_below_{break_val}"] = sum(
            [evt.end - evt.start for evt in mode_events if evt.value <= break_val]
        )
    return output
