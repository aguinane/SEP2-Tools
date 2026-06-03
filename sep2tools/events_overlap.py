from .event_models import DERControl, DERModeControl


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


def split_overlapping_events(events: list[DERModeControl]) -> list[DERModeControl]:
    # TODO: Handle adding random start and duration values without overlap.
    new_events = []
    times = [(x.intervalStart, x.intervalStart + x.intervalDuration) for x in events]
    for xstart, xend in non_overlapping_periods(times):
        for evt in events:
            evt_start = evt.intervalStart
            evt_end = evt.intervalStart + evt.intervalDuration
            if evt_start >= xend:
                continue
            if evt_end <= xstart:
                continue
            nevt = evt.model_copy()
            nevt.intervalStart = xstart
            nevt.intervalDuration = xend - xstart
            new_events.append(nevt)
    return new_events


def condense_mode_events(events: list[DERModeControl]) -> list[DERModeControl]:
    # First split the events
    events = split_overlapping_events(events)

    # Then pick lowest primacy, or latest creation time
    event_starts = {}
    for evt in events:
        if evt.intervalStart not in event_starts:
            event_starts[evt.intervalStart] = []
        event_starts[evt.intervalStart].append(evt)

    new_events = []
    for start in event_starts:
        xevents = sorted(
            event_starts[start], key=lambda x: (x.programPrimacy, -x.creationTime)
        )
        new_events.append(xevents[0])

    # Finally, restitch any events that were split that can be joined back together
    new_events2 = []
    for i, evt in enumerate(new_events):
        if i == 0:
            new_events2.append(evt)
            continue
        prev_evt = new_events[i - 1]
        if prev_evt.mRID == evt.mRID:
            evt.intervalStart = prev_evt.intervalStart  # Set to start from prev
            new_events2.pop()  # Remove the previous
        new_events2.append(evt)
    return new_events2


def condense_events(events: list[DERControl]) -> dict[str, list[DERModeControl]]:
    schedule = {}
    for evt in events:
        for cntrl in evt.controls:
            mode = cntrl.mode
            if mode not in schedule:
                schedule[mode] = []
            me = DERModeControl(
                mRID=evt.mRID,
                programName=evt.programName,
                programPrimacy=evt.programPrimacy,
                currentStatus=evt.currentStatus,
                statusTime=evt.statusTime,
                isDefault=evt.isDefault,
                creationTime=evt.creationTime,
                intervalStart=evt.intervalStart,
                intervalDuration=evt.intervalDuration,
                randomizeStart=evt.randomizeStart,
                randomizeDuration=evt.randomizeDuration,
                controlMode=cntrl.mode,
                controlValue=cntrl.value,
                controlMultiplier=cntrl.multiplier,
            )
            schedule[mode].append(me)

    for mode in schedule:
        schedule[mode] = condense_mode_events(schedule[mode])
    return schedule
