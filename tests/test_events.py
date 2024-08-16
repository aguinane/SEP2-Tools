from sep2tools.events import DERControl, DERControlBase, condense_events

EXAMPLE_EVENTS = [
    DERControl(
        mRID="1A",
        creationTime=0,
        currentStatus=0,
        start=50,
        duration=50,
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        primacy=1,
    ),
    DERControl(
        mRID="1B",
        creationTime=3,
        currentStatus=0,
        start=50,
        duration=50,
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        primacy=1,
    ),
    DERControl(
        mRID="2",
        creationTime=0,
        currentStatus=0,
        start=100,
        duration=50,
        controls=[DERControlBase(mode="opModExpLimW", value=15, multiplier=3)],
        primacy=1,
    ),
    DERControl(
        mRID="3",
        creationTime=0,
        currentStatus=0,
        start=120,
        duration=50,
        controls=[DERControlBase(mode="opModExpLimW", value=20, multiplier=3)],
        primacy=0,
    ),
    DERControl(
        mRID="4",
        creationTime=0,
        currentStatus=0,
        start=150,
        duration=50,
        controls=[DERControlBase(mode="opModExpLimW", value=15, multiplier=3)],
        primacy=1,
    ),
    DERControl(
        mRID="5",
        creationTime=0,
        currentStatus=0,
        start=250,
        duration=50,
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        primacy=1,
    ),
]


def test_event_condensing():
    """Test event primacy correct"""

    schedule = condense_events(EXAMPLE_EVENTS)
    modes = list(schedule.keys())
    assert modes == ["opModExpLimW", "opModImpLimW"]

    exp_evts = schedule["opModExpLimW"]

    # Check that the later event is chosen
    assert "1A" not in [x.mrid for x in exp_evts]
    assert "1B" in [x.mrid for x in exp_evts]

    # Check that Evt 2 is finished early
    b = exp_evts[1]
    assert b.mrid == "2"
    assert b.end == 120

    # Check that Evt 4 is started late
    c = exp_evts[3]
    assert c.mrid == "4"
    assert c.start == 170  # and not 150
    assert c.end == 200
