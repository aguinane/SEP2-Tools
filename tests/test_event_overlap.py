from sep2tools.event_models import (
    CurrentStatus,
    DERControl,
    DERControlBase,
)
from sep2tools.events_overlap import condense_events

EXAMPLE_EVENTS = [
    DERControl(
        mRID="1A",
        creationTime=0,
        currentStatus=CurrentStatus(0),
        intervalStart=50,
        intervalDuration=50,
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        programPrimacy=1,
    ),
    DERControl(
        mRID="1B",
        creationTime=3,
        currentStatus=CurrentStatus(0),
        intervalStart=50,
        intervalDuration=50,
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        programPrimacy=1,
    ),
    DERControl(
        mRID="2",
        creationTime=0,
        currentStatus=CurrentStatus(0),
        intervalStart=100,
        intervalDuration=50,
        controls=[DERControlBase(mode="opModExpLimW", value=15, multiplier=3)],
        programPrimacy=1,
    ),
    DERControl(
        mRID="3",
        creationTime=0,
        currentStatus=CurrentStatus(0),
        intervalStart=120,
        intervalDuration=50,
        controls=[DERControlBase(mode="opModExpLimW", value=20, multiplier=3)],
        programPrimacy=0,
    ),
    DERControl(
        mRID="4",
        creationTime=0,
        currentStatus=CurrentStatus(0),
        intervalStart=150,
        intervalDuration=50,
        controls=[DERControlBase(mode="opModExpLimW", value=15, multiplier=3)],
        programPrimacy=1,
    ),
    DERControl(
        mRID="5",
        creationTime=0,
        currentStatus=CurrentStatus(0),
        intervalStart=250,
        intervalDuration=50,
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        programPrimacy=1,
    ),
]


def test_event_condensing():
    """Test event primacy correct"""

    schedule = condense_events(EXAMPLE_EVENTS)
    modes = list(schedule.keys())
    assert modes == ["opModExpLimW", "opModImpLimW"]

    exp_evts = schedule["opModExpLimW"]

    # Check that the later event is chosen
    assert "1A" not in [x.mRID for x in exp_evts]
    assert "1B" in [x.mRID for x in exp_evts]

    # Check that Evt 2 is finished early
    b = exp_evts[1]
    assert b.mRID == "2"
    assert b.intervalEnd == 120  # and not 150

    # Check that Evt 4 is started late
    c = exp_evts[3]
    assert c.mRID == "4"
    assert c.intervalStart == 170  # and not 150
    assert c.intervalDuration == 30
