from sep2tools.eventsdb import add_events, clear_old_events
from sep2tools.examples import example_controls, example_default_control

example_events = [*example_controls(), example_default_control()]
for evt in example_events:
    print(evt)

add_events(example_events)
clear_old_events(days_to_keep=0)
