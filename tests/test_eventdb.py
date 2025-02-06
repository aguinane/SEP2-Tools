from sep2tools.eventsdb import (
    add_events,
    clear_old_events,
    delete_event,
    get_day_mode_events,
    get_ders,
    get_event,
    get_modes,
    update_mode_events,
)
from sep2tools.examples import example_controls, example_default_control
from sep2tools.times import current_date


def test_todays_events():
    """Test events for today have correct seconds"""
    today = current_date()
    for der in get_ders():
        for mode in get_modes(der):
            num_seconds = 0
            for evt in get_day_mode_events(der, mode, today):
                duration = evt.end - evt.start
                num_seconds += duration
            assert num_seconds == 86400


def test_event_creation():
    """Test events are created and deleted from DB"""
    exp1 = example_default_control()
    exp2 = example_controls(num=1)[0]
    examples = [exp1, exp2]
    for exp in examples:
        mrid = exp.mRID
        add_events([exp])
        evt = get_event(mrid=mrid)
        assert exp == evt
        delete_event(mrid)


def test_event_clearing():
    """Test old events are deleted from DB"""
    clear_old_events()


def test_mode_event_updates():
    """Test old events are deleted from DB"""
    evt = example_default_control()
    add_events([evt])
    update_mode_events()
