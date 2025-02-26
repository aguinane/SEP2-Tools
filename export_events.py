from datetime import date

import plotly.express as px
import polars as pl

from sep2tools.eventsdb import (
    add_enrolment,
    add_events,
    clear_old_events,
    get_modes_data,
    update_daily_summaries,
    update_mode_events,
)
from sep2tools.examples import example_controls, example_default_control
from sep2tools.times import current_date


def write_example_events(der: str, program: str):
    example_events = [
        *example_controls(program=program),
        example_default_control(program=program),
    ]
    add_events(example_events)
    add_enrolment(der, program)
    update_mode_events()
    update_daily_summaries()
    clear_old_events(days_to_keep=3.0)


def chart_der_controls(der: str, day: date | None = None):
    data = get_modes_data(der, day)
    df = pl.DataFrame(data)
    fig = px.line(df, x="time", y="value", color="mode", title=der)
    fig.update_layout(
        xaxis={"title": ""},
        yaxis={"title": ""},
    )
    return fig


if __name__ == "__main__":
    der = "EXAMPLEDER"
    program = "EXAMPLEPRG"
    write_example_events(der, program)
    today = current_date()
    fig = chart_der_controls(der)
    fig.show()
