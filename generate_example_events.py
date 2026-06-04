from sep2tools.event_examples import example_controls, example_default_control
from sep2tools.events_db import (
    cleanup_defaults,
    delete_superseded,
    get_mode_events,
    get_program_modes,
    supersede_overlapping,
)
from sep2tools.events_overlap import condense_mode_events

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
    events = get_mode_events(program=program, mode=mode)
    events = condense_mode_events(events)
    print(events[0])
    print(events[-1])
