from datetime import date

import plotly.express as px

from sep2tools.event_analysis import get_modes_dataframe
from sep2tools.eventsdb import (
    add_enrolment,
    add_events,
    clear_old_events,
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


def chart_der_controls(der: str, day: date | None = None):
    df = get_modes_dataframe(der, day)
    fig = px.line(df, x="time", y="value", color="mode", title=der)
    fig.update_layout(
        xaxis={"title": ""},
        yaxis={"title": ""},
    )
    return fig


today = current_date()
fig = chart_der_controls(der, today)
fig.show()
