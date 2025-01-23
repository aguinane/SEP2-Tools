from datetime import datetime, timezone
from random import randint

from sep2tools import generate_mrid
from sep2tools.models import (
    DateTimeInterval,
    DERControl,
    DERControlBase,
    EventStatus,
    ProgramInfo,
)
from sep2tools.times import next_interval


def example_control(
    start: int, duration: int = 300, program: str = "EXAMPLEPRG", primacy: int = 1
) -> DERControl:
    mrid = generate_mrid(0, group=False)
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    creation_time = int(now_utc.timestamp())
    exp_limit = randint(15, 100) * 100
    imp_limit = randint(15, 100) * 100
    evt = DERControl(
        mRID=mrid,
        creationTime=creation_time,
        EventStatus=EventStatus(currentStatus=0),
        interval=DateTimeInterval(start=start, duration=duration),
        randomizeStart=10,
        controls=[
            DERControlBase(mode="csipaus:opModExpLimW", value=exp_limit),
            DERControlBase(mode="csipaus:opModImpLimW", value=imp_limit),
        ],
        ProgramInfo=ProgramInfo(program=program, primacy=primacy),
    )
    return evt


def example_controls(num: int = 6) -> list[DERControl]:
    events = []
    start = next_interval(5)
    duration = 300
    for _ in range(0, num):
        evt = example_control(start, duration)
        events.append(evt)
        start = start + duration
    return events
