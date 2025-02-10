from datetime import date

import plotly.express as px
import polars as pl

from sep2tools.event_analysis import get_mode_day_distribution, get_modes_data
from sep2tools.eventsdb import (
    add_enrolment,
    add_events,
    clear_old_events,
    get_mode_event_days,
    get_modes,
    update_mode_events,
)
from sep2tools.examples import example_controls, example_default_control
from sep2tools.times import current_date

der = "EXAMPLEDER"
program = "EXAMPLEPRG"
example_events = [
    *example_controls(program=program, num=24),
    example_default_control(program=program),
]
add_events(example_events)
add_enrolment(der, program)
update_mode_events()
clear_old_events(days_to_keep=3.0)

for mode in get_modes(der):
    for day in get_mode_event_days(der, mode):
        print(der, mode, day)
        try:
            res = get_mode_day_distribution(der, mode, day)
        except ValueError:
            continue
        print(res)


def chart_der_controls(der: str, day: date | None = None):
    data = get_modes_data(der, day)
    df = pl.DataFrame(data)
    fig = px.line(df, x="time", y="value", color="mode", title=der)
    fig.update_layout(
        xaxis={"title": ""},
        yaxis={"title": ""},
    )
    return fig


today = current_date()
fig = chart_der_controls(der, today)
fig.show()
