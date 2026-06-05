from sep2tools.event_examples import example_default_control
from sep2tools.events_clean import get_mode_event_values
from sep2tools.events_db import add_events, cleanup_events, get_program_modes


def test_get_mode_event_values_example():
    program = "EXAMPLEPRG"
    example_events = [
        example_default_control(program=program),
    ]
    add_events(example_events)
    cleanup_events()
    modes = get_program_modes(program=program)
    mode = modes[0]
    events = get_mode_event_values(program=program, mode=mode, retro_hours=12)
    assert len(events) > 0


def test_get_mode_event_values_empty():
    program = "NOTAPRG"
    mode = "NOTAMODE"
    events = get_mode_event_values(program=program, mode=mode, retro_hours=12)
    assert len(events) == 0
