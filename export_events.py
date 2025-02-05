from sep2tools.eventsdb import (
    add_events,
    clear_old_events,
    get_mode_events,
    get_modes,
)
from sep2tools.examples import example_controls, example_default_control

example_events = [*example_controls(), example_default_control()]
add_events(example_events)
clear_old_events(days_to_keep=0)

der = "EXAMPLEDER"
for mode in get_modes(der):
    print(mode)
    events = get_mode_events(der, mode)
    for evt in events:
        print(evt)
