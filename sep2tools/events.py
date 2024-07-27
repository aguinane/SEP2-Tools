from enum import IntEnum

from pydantic import BaseModel


class CurrentStatus(IntEnum):
    Scheduled = 0
    Active = 1
    Cancelled = 2
    CancelledWithRadomization = 3
    Superseded = 4


class Status(IntEnum):
    EventReceived = 1
    EventStarted = 2
    EventCompleted = 3
    Superseded = 4
    EventCancelled = 6
    EventSuperseded = 7


class DERControlBase(BaseModel):
    mode: str
    value: int
    multiplier: int = 0


class DERControl(BaseModel):
    mRID: str
    creationTime: int
    currentStatus: CurrentStatus
    start: int
    duration: int
    randomizeStart: int = 0
    randomizeDuration: int = 0
    controls: list[DERControlBase]
    primacy: int


class ModeEvent(BaseModel):
    mrid: str
    primacy: int
    creation_time: int
    start: int
    end: int
    value: int
    rand_start: int
    rand_dur: int


def non_overlapping_periods(events: list[tuple[int, int]]) -> list[tuple[int, int]]:
    time_points = []
    for start, end in events:
        time_points.append((start, "start"))
        time_points.append((end, "end"))
    time_points.sort()

    unique_intervals = []
    current_interval_start = None
    active_events = 0
    for i, (time, typ) in enumerate(time_points):
        if current_interval_start is not None and time > current_interval_start:
            unique_intervals.append((current_interval_start, time))
        if typ == "start":
            active_events += 1
        elif typ == "end":
            active_events -= 1
        current_interval_start = time

    split_events = set()
    for interval_start, interval_end in unique_intervals:
        for start, end in events:
            if start < interval_end and end > interval_start:
                split_events.add((max(start, interval_start), min(end, interval_end)))
    return sorted(list(split_events))


def split_overlapping_events(events):
    # TODO: Handle adding random start and duration values without overlap.
    new_events = []
    times = [(x.start, x.end) for x in events]
    for xstart, xend in non_overlapping_periods(times):
        for evt in events:
            if evt.start >= xend:
                continue
            if evt.end <= xstart:
                continue
            nevt = evt.copy()
            nevt.start = xstart
            nevt.end = xend
            new_events.append(nevt)
    return new_events


def condense_events(events):
    # First split the events
    events = split_overlapping_events(events)

    # Then pick lowest primacy, or latest creation time
    event_starts = {}
    for evt in events:
        if evt.start not in event_starts:
            event_starts[evt.start] = []
        event_starts[evt.start].append(evt)

    new_events = []
    for start in event_starts:
        xevents = sorted(
            event_starts[start], key=lambda x: (x.primacy, -x.creation_time)
        )
        new_events.append(xevents[0])

    return new_events


EXAMPLE_EVENTS = [
    DERControl(
        mRID="1",
        creationTime=0,
        currentStatus=0,
        start=5,
        duration=5,
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
        start=10,
        duration=5,
        controls=[DERControlBase(mode="opModExpLimW", value=1.5, multiplier=3)],
        primacy=1,
    ),
    DERControl(
        mRID="2B",
        creationTime=0,
        currentStatus=0,
        start=12,
        duration=5,
        controls=[DERControlBase(mode="opModExpLimW", value=2.0, multiplier=3)],
        primacy=0,
    ),
    DERControl(
        mRID="3",
        creationTime=0,
        currentStatus=0,
        start=15,
        duration=5,
        controls=[DERControlBase(mode="opModExpLimW", value=1.5, multiplier=3)],
        primacy=1,
    ),
]

schedule = {}
for evt in EXAMPLE_EVENTS:
    mrid = evt.mRID
    primacy = evt.primacy
    creation_time = evt.creationTime
    start = evt.start
    end = evt.start + evt.duration
    rand_start = evt.randomizeStart
    rand_dur = evt.randomizeDuration
    for cntrl in evt.controls:
        value = cntrl.value * (10**cntrl.multiplier)
        mode = cntrl.mode
        if mode not in schedule:
            schedule[mode] = []

        me = ModeEvent(
            mrid=mrid,
            primacy=primacy,
            creation_time=creation_time,
            start=start,
            end=end,
            value=value,
            rand_start=rand_start,
            rand_dur=rand_dur,
        )
        schedule[mode].append(me)


for mode in schedule:
    print()
    print(mode)
    print()
    events = schedule[mode]
    for x in events:
        print(x)
    events = condense_events(events)
    print("becomes ...")
    for x in events:
        print(x)
