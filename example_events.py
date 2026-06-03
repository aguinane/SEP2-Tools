from sep2tools.event_examples import example_controls, example_default_control
from sep2tools.events_db import add_events, cleanup_defaults, get_events

if __name__ == "__main__":
    der = "EXAMPLEDER"
    program = "EXAMPLEPRG"
    example_events = [
        *example_controls(program=program),
        example_default_control(program=program),
    ]
    add_events(example_events)
    cleanup_defaults()
    for evt in get_events(program=program):
        print(evt)
