from sep2tools.eventsdb import add_events
from sep2tools.models import (
    DateTimeInterval,
    DERControl,
    DERControlBase,
    EventStatus,
    ProgramInfo,
)

EXAMPLE_EVENTS = [
    DERControl(
        mRID="1A",
        creationTime=0,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=50, duration=50),
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        ProgramInfo=ProgramInfo(primacy=1),
    ),
    DERControl(
        mRID="1B",
        creationTime=3,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=50, duration=50),
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        ProgramInfo=ProgramInfo(primacy=1),
    ),
    DERControl(
        mRID="2",
        creationTime=0,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=100, duration=50),
        controls=[DERControlBase(mode="opModExpLimW", value=15, multiplier=3)],
        ProgramInfo=ProgramInfo(primacy=1),
    ),
    DERControl(
        mRID="3",
        creationTime=0,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=120, duration=50),
        controls=[DERControlBase(mode="opModExpLimW", value=20, multiplier=3)],
        ProgramInfo=ProgramInfo(primacy=0),
    ),
    DERControl(
        mRID="4",
        creationTime=0,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=150, duration=50),
        controls=[DERControlBase(mode="opModExpLimW", value=15, multiplier=3)],
        ProgramInfo=ProgramInfo(primacy=1),
    ),
    DERControl(
        mRID="5",
        creationTime=0,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=250, duration=50),
        controls=[
            DERControlBase(mode="opModExpLimW", value=1500),
            DERControlBase(mode="opModImpLimW", value=1500),
        ],
        ProgramInfo=ProgramInfo(primacy=1),
    ),
]


add_events(EXAMPLE_EVENTS)
