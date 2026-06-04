from sep2tools.event_examples import example_controls, example_default_control
from sep2tools.events_db import add_events, remove_old_events


def test_create_cleanup_events():
    """Create example events, add to db, then remove old events"""
    program = "EXAMPLEPRG"
    example_events = [
        *example_controls(program=program),
        example_default_control(program=program),
    ]
    add_events(example_events)
    remove_old_events(retro_hours=24.0)
