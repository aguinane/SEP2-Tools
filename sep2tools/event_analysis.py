import pandas as pd

from .eventsdb import (
    get_mode_events,
    get_modes,
)
from .times import timestamp_local_dt


def get_modes_dataframe(der: str) -> pd.DataFrame:
    data = []
    for mode in get_modes(der):
        for evt in get_mode_events(der, mode):
            start = timestamp_local_dt(evt.start).replace(tzinfo=None)
            item = {"mode": mode, "time": start, "value": evt.value}
            data.append(item)
            short_end = min(evt.end, evt.start + 43200)
            end = timestamp_local_dt(short_end).replace(tzinfo=None)
            item = {"mode": mode, "time": end, "value": evt.value}
            data.append(item)
    return pd.DataFrame(data)
