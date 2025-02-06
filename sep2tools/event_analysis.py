from datetime import date

import pandas as pd

from .eventsdb import get_day_mode_events, get_mode_events, get_modes
from .times import timestamp_local_dt


def get_modes_dataframe(der: str, day: date | None = None) -> pd.DataFrame:
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
    return pd.DataFrame(data)
