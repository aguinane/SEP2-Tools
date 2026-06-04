from sep2tools.event_examples import example_controls, example_default_control
from sep2tools.events_clean import get_mode_event_values
from sep2tools.events_db import (
    cleanup_defaults,
    delete_superseded,
    get_program_modes,
    supersede_overlapping,
)

if __name__ == "__main__":
    der = "EXAMPLEDER"
    program = "EXAMPLEPRG"
    example_events = [
        *example_controls(program=program),
        example_default_control(program=program),
    ]
    # add_events(example_events)
    cleanup_defaults()
    supersede_overlapping()
    delete_superseded()

    modes = get_program_modes(program=program)
    mode = modes[0]
    print(f"Events for mode {mode}:")
    event_values = get_mode_event_values(program=program, mode=mode)
    for dt, val in event_values:
        print(f"{dt}: {val}")
