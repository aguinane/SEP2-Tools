from datetime import datetime, timezone
from random import randint

from sep2tools import generate_mrid
from sep2tools.eventsdb import get_default_event
from sep2tools.models import (
    DateTimeInterval,
    DERControl,
    DERControlBase,
    EventStatus,
    ProgramInfo,
)
from sep2tools.times import next_interval, timestamp_local_dt


def example_control(
    start: int, duration: int = 300, program: str = "EXAMPLEPRG", primacy: int = 1
) -> DERControl:
    mrid = generate_mrid(0, group=False)
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    creation_time = int(now_utc.timestamp())
    hour = timestamp_local_dt(start).hour
    exp_min = 15 if 9 <= hour < 16 else 100
    imp_min = 15 if 16 <= hour < 21 else 100
    exp_limit = randint(exp_min, 100) * 100
    imp_limit = randint(imp_min, 100) * 100
    evt = DERControl(
        mRID=mrid,
        creationTime=creation_time,
        EventStatus=EventStatus(currentStatus=0),  # Scheduled
        interval=DateTimeInterval(start=start, duration=duration),
        randomizeStart=10,
        controls=[
            DERControlBase(mode="csipaus:opModExpLimW", value=exp_limit),
            DERControlBase(mode="csipaus:opModImpLimW", value=imp_limit),
        ],
        ProgramInfo=ProgramInfo(program=program, primacy=primacy),
    )
    return evt


def example_default_control(
    program: str = "EXAMPLEPRG", primacy: int = 1
) -> DERControl:
    # Max Primacy is 255
    # set the default above this so that default controls are always after events
    # but still have correct order if multiple defaults
    default_primacy = 256 + primacy
    mrid = generate_mrid(0, group=False)
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    creation_time = int(now_utc.timestamp())

    # In order to not break tests - set first default control at least one day ago
    if get_default_event(program) is None:
        creation_time = creation_time - 86400
    # A default starts when it is created
    start = creation_time
    # If replaced the new one will have a newer creation time and supersede
    # So set end to way in future
    duration = 999999999
    exp_limit = 1500
    imp_limit = 1500
    evt = DERControl(
        mRID=mrid,
        creationTime=creation_time,
        EventStatus=EventStatus(currentStatus=1),  # Active
        interval=DateTimeInterval(start=start, duration=duration),
        randomizeStart=10,
        controls=[
            DERControlBase(mode="csipaus:opModExpLimW", value=exp_limit),
            DERControlBase(mode="csipaus:opModImpLimW", value=imp_limit),
        ],
        ProgramInfo=ProgramInfo(program=program, primacy=default_primacy),
    )
    return evt


def example_controls(program: str = "EXAMPLEPRG", num: int = 288) -> list[DERControl]:
    events = []
    start = next_interval(5)
    duration = 300
    for _ in range(0, num):
        evt = example_control(start, duration, program=program)
        events.append(evt)
        start = start + duration
    return events
