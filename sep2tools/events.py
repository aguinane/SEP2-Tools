from .models import DERControl, ModeEvent


def non_overlapping_periods(events: list[tuple[int, int]]) -> list[tuple[int, int]]:
    time_points = []
    for start, end in events:
        time_points.append((start, "start"))
        time_points.append((end, "end"))
    time_points.sort()

    unique_intervals = []
    current_interval_start = None
    active_events = 0
    for time, typ in time_points:
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


def split_overlapping_events(events: list[ModeEvent]) -> list[ModeEvent]:
    # TODO: Handle adding random start and duration values without overlap.
    new_events = []
    times = [(x.start, x.end) for x in events]
    for xstart, xend in non_overlapping_periods(times):
        for evt in events:
            if evt.start >= xend:
                continue
            if evt.end <= xstart:
                continue
            nevt = evt.model_copy()
            nevt.start = xstart
            nevt.end = xend
            new_events.append(nevt)
    return new_events


def condense_mode_events(events: list[ModeEvent]) -> list[ModeEvent]:
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

    # Finally, restitch any events that were split that can be joined back together
    new_events2 = []
    for i, evt in enumerate(new_events):
        if i == 0:
            new_events2.append(evt)
            continue
        prev_evt = new_events[i - 1]
        if prev_evt.mrid == evt.mrid:
            evt.start = prev_evt.start  # Set to start from prev
            new_events2.pop()  # Remove the previous
        new_events2.append(evt)
    return new_events2


def condense_events(events: list[DERControl]) -> dict[str, list[ModeEvent]]:
    schedule = {}
    for evt in events:
        mrid = evt.mRID
        primacy = evt.ProgramInfo.primacy
        creation_time = evt.creationTime
        start = evt.interval.start
        end = evt.interval.start + evt.interval.duration
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
        schedule[mode] = condense_mode_events(schedule[mode])
    return schedule
