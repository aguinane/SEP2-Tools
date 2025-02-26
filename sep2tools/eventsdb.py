import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlite_utils import Database

from .events import condense_events
from .models import (
    DateTimeInterval,
    DERControl,
    DERControlBase,
    EventStatus,
    ModeEvent,
    ProgramInfo,
)
from .times import (
    current_date,
    day_time_range,
    event_days,
    next_interval,
    timestamp_local_dt,
)

load_dotenv()
log = logging.getLogger(__name__)
events_dir = os.getenv("EVENTS_DB_DIR", "")
EVENTS_DB_DIR = Path(events_dir)
EVENTS_DB = EVENTS_DB_DIR / "events.db"

DEFAULT_DIST_BREAKS = (1500, 5000, 10000)


EVENT_COLS = {
    "mRID": str,
    "creationTime": int,
    "currentStatus": int,
    "start": int,
    "duration": int,
    "randomizeStart": int,
    "randomizeDuration": int,
    "controls": dict,
    "program": str,
    "primacy": int,
}

ENROLMENT_COLS = {
    "der": str,
    "program": str,
}

MODE_EVENT_COLS = {
    "der": str,
    "mode": str,
    "start": int,
    "end": int,
    "value": int,
    "creation_time": int,
    "rand_start": int,
    "rand_dur": int,
    "mrid": str,
    "primacy": int,
}

DAILY_SUMMARY_COLS = {
    "der": str,
    "day": str,
    "mode": str,
    "min_value": int,
    "max_value": int,
    "s_at_min": int,
    "s_at_max": int,
    "s_at_or_below_1500": int,
    "s_at_or_below_5000": int,
    "s_at_or_below_10000": int,
}


def create_db() -> Path:
    if EVENTS_DB.exists():
        return EVENTS_DB
    db = Database(EVENTS_DB, strict=True)
    events = db["events"]
    events.create(
        EVENT_COLS,
        pk="mRID",
        not_null=["creationTime", "start", "duration", "controls"],
        if_not_exists=True,
    )
    enrolments = db["enrolments"]
    enrolments.create(
        ENROLMENT_COLS,
        pk=("der", "program"),
        not_null=("der", "program"),
        if_not_exists=True,
    )
    mode_events = db["mode_events"]
    mode_events.create(
        MODE_EVENT_COLS,
        pk=("der", "mode", "start", "end"),
        not_null=("der", "mode", "start", "end", "value"),
        if_not_exists=True,
    )
    daily_summary = db["daily_summary"]
    daily_summary.create(
        DAILY_SUMMARY_COLS,
        pk=("der", "day", "mode"),
        not_null=("der", "day", "mode", "min_value", "max_value"),
        if_not_exists=True,
    )
    return EVENTS_DB


def add_enrolment(der: str, program: str):
    db_path = create_db()
    item = {"der": der, "program": program}
    db = Database(db_path)
    db["enrolments"].insert(item, replace=True)


def get_ders() -> set[str]:
    db_path = create_db()
    db = Database(db_path)
    sql = "SELECT DISTINCT der FROM enrolments ORDER BY der"
    ders = set()
    with db.conn:
        res = db.query(sql)
        for x in res:
            der = x["der"]
            ders.add(der)
    return ders


def get_enrolments() -> dict[str, list[str]]:
    db_path = create_db()
    db = Database(db_path)
    sql = "SELECT der, program FROM enrolments ORDER BY der, program"
    ders = {}
    with db.conn:
        res = db.query(sql)
        for x in res:
            der = x["der"]
            program = x["program"]
            if der not in ders:
                ders[der] = []
            ders[der].append(program)
    return ders


def add_events(events: list[DERControl]):
    db_path = create_db()
    db = Database(db_path)
    records = [
        {
            "mRID": evt.mRID,
            "creationTime": evt.creationTime,
            "currentStatus": evt.EventStatus.currentStatus,
            "start": evt.interval.start,
            "duration": evt.interval.duration,
            "randomizeStart": evt.randomizeStart,
            "randomizeDuration": evt.randomizeDuration,
            "controls": [x.model_dump() for x in evt.controls],
            "program": evt.ProgramInfo.program,
            "primacy": evt.ProgramInfo.primacy,
        }
        for evt in events
    ]
    db["events"].insert_all(records, replace=True)


def update_mode_events():
    update_old_default_events()  # Should reduce conflicts to calculate
    clear_mode_events()
    enrolments = get_enrolments()
    for der, programs in enrolments.items():
        raw_events = []
        for prg in programs:
            prg_events = get_events(prg)
            raw_events.extend(prg_events)

        clean_events = condense_events(raw_events)
        for mode, events in clean_events.items():
            add_mode_events(der, mode, events)


def daily_summary_exists(der: str, mode: str, day: str) -> bool:
    sql = "SELECT * FROM daily_summary WHERE der = :der AND mode = :mode AND day = :day"
    db_path = create_db()
    db = Database(db_path)
    with db.conn:
        res = db.query(sql, {"der": der, "mode": mode, "day": day})
        for _ in res:
            return True
    return False


def add_daily_summaries(records: list[dict]):
    db_path = create_db()
    db = Database(db_path)
    db["daily_summary"].insert_all(records, replace=True)


def add_mode_events(
    der: str,
    mode: str,
    events: list[ModeEvent],
):
    db_path = create_db()
    db = Database(db_path)
    records = [
        {
            "der": der,
            "mode": mode,
            "start": evt.start,
            "end": evt.end,
            "value": evt.value,
            "creation_time": evt.creation_time,
            "rand_start": evt.rand_start,
            "rand_dur": evt.rand_dur,
            "mrid": evt.mrid,
            "primacy": evt.primacy,
        }
        for evt in events
    ]
    db["mode_events"].insert_all(records, replace=True)


def flattened_event_to_object(evt: dict) -> DERControl:
    status = EventStatus(currentStatus=evt["currentStatus"])
    interval = DateTimeInterval(start=evt["start"], duration=evt["duration"])
    program = ProgramInfo(program=evt["program"], primacy=evt["primacy"])
    controls_list = json.loads(evt["controls"])
    controls = [DERControlBase(**x) for x in controls_list]
    return DERControl(
        mRID=evt["mRID"],
        EventStatus=status,
        creationTime=evt["creationTime"],
        interval=interval,
        randomizeStart=evt["randomizeStart"],
        randomizeDuration=evt["randomizeDuration"],
        controls=controls,
        ProgramInfo=program,
    )


def get_event(mrid: str) -> DERControl | None:
    db_path = create_db()

    sql = "SELECT * FROM events WHERE mRID = :mrid"
    db = Database(db_path)
    with db.conn:
        res = db.query(sql, {"mrid": mrid})
        for x in res:
            item = flattened_event_to_object(x)
            return item
    return None


def get_default_event(program: str) -> DERControl | None:
    db_path = create_db()
    sql = """SELECT * FROM events
    WHERE duration = 999999999 AND primacy > 255 AND program = :prog
    ORDER BY creationTime DESC
    """
    db = Database(db_path)
    with db.conn:
        res = db.query(sql, {"prog": program})
        for x in res:
            item = flattened_event_to_object(x)
            return item
    return None


def delete_event(mrid: str):
    db_path = EVENTS_DB
    sql = "DELETE FROM events WHERE mRID = :mrid"
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"mrid": mrid})


def update_event_status(mrid: str, new_status: int):
    db_path = EVENTS_DB
    sql = "UPDATE events SET currentStatus = :status WHERE mRID = :mrid"
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"mrid": mrid, "status": new_status})


def update_event_controls(mrid: str, control_json: str):
    db_path = EVENTS_DB
    sql = "UPDATE events SET controls = :ctrl WHERE mRID = :mrid"
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"mrid": mrid, "ctrl": control_json})


def get_events(program: str) -> list[DERControl]:
    sql = "SELECT * FROM events WHERE program = :prg ORDER BY start, creationTime"
    db_path = create_db()
    db = Database(db_path)
    events = []
    with db.conn:
        res = db.query(sql, {"prg": program})
        for x in res:
            item = flattened_event_to_object(x)
            events.append(item)
    return events


def get_programs() -> list[str]:
    sql = "SELECT DISTINCT program FROM events ORDER BY program"
    db_path = create_db()
    db = Database(db_path)
    res = db.query(sql)
    return [x["program"] for x in res]


def get_modes(der: str) -> list[str]:
    sql = "SELECT DISTINCT mode FROM mode_events WHERE der = :der ORDER BY 1"
    db_path = create_db()
    db = Database(db_path)
    res = db.query(sql, {"der": der})
    return [x["mode"] for x in res]


def get_mode_events(der: str, mode: str) -> list[ModeEvent]:
    sql = "SELECT * FROM mode_events WHERE der = :der and mode = :mode ORDER BY start"
    db_path = create_db()
    db = Database(db_path)
    events = []
    with db.conn:
        res = db.query(sql, {"der": der, "mode": mode})
        for x in res:
            item = ModeEvent(**x)
            events.append(item)
    return events


def get_mode_event_range(der: str, mode: str) -> tuple[int, int]:
    sql = """SELECT MIN(start) as start, MAX(end) as end 
    FROM mode_events 
    WHERE primacy < 255
    AND der = :der and mode = :mode
    """
    db_path = create_db()
    db = Database(db_path)
    res = list(db.query(sql, {"der": der, "mode": mode}))
    row = res[0]
    start = row["start"]
    end = row["end"]
    return start, end


def get_mode_event_days(der: str, mode: str) -> list[date]:
    start, end = get_mode_event_range(der, mode)
    return event_days(start, end)


def get_day_mode_events(der: str, mode: str, day: date) -> list[ModeEvent]:
    start, end = day_time_range(day)
    sql = """SELECT * FROM mode_events 
    WHERE der = :der and mode = :mode 
    AND (start >= :start OR end >= :start)
    AND (end <= :end OR start <= :end)
    ORDER BY start"""
    db_path = create_db()
    db = Database(db_path)
    events = []
    with db.conn:
        res = db.query(sql, {"der": der, "mode": mode, "start": start, "end": end})
        for x in res:
            item = ModeEvent(**x)
            if item.start < start:
                item.start = start
            if item.end > end:
                item.end = end
            events.append(item)
    return events


def clear_mode_events():
    sql = "DELETE FROM mode_events"
    db_path = EVENTS_DB
    db = Database(db_path)
    with db.conn:
        db.execute(sql)


def update_old_default_events():
    """Default events can not be cancelled so modify duration"""
    db_path = create_db()
    sql = """SELECT * FROM events WHERE duration = 999999999 AND primacy > 255
    AND program = :program ORDER BY start DESC"""
    db = Database(db_path)

    for program in get_programs():
        with db.conn:
            res = list(db.query(sql, {"program": program}))
            for i, evt in enumerate(res):
                if i == 0:
                    continue  # Do nothing with most recent default event

                mrid = evt["mRID"]
                start = evt["start"]
                prev_start = res[i - 1]["start"]
                new_duration = prev_start - start
                update_sql = "UPDATE events SET duration = :duration WHERE mRID = :mrid"
                db.execute(update_sql, {"mrid": mrid, "duration": new_duration})


def get_modes_data(der: str, day: date | None = None) -> list[dict[str, Any]]:
    data = []
    # Ignore events that are 25+ hours in future
    # If you do not - the default control runs for years
    event_cutoff = next_interval() + 90000
    for mode in get_modes(der):
        if day:
            mode_events = get_day_mode_events(der, mode, day)
        else:
            mode_events = get_mode_events(der, mode)
        for evt in mode_events:
            evt_start = evt.start
            start = timestamp_local_dt(evt_start).replace(tzinfo=None)
            item = {"mode": mode, "time": start, "value": evt.value}
            data.append(item)
            evt_end = evt.end
            if evt_end > event_cutoff:
                evt_end = max(event_cutoff, evt_start)
            end = timestamp_local_dt(evt_end).replace(tzinfo=None)
            item = {"mode": mode, "time": end, "value": evt.value}
            data.append(item)
    return data


def get_mode_day_distribution(
    der: str, mode: str, day: date, breaks: tuple[int] = DEFAULT_DIST_BREAKS
):
    mode_events = get_day_mode_events(der, mode, day)
    max_value = max([x.value for x in mode_events])
    min_value = min([x.value for x in mode_events])
    num_seconds = 0

    for evt in mode_events:
        duration = evt.end - evt.start
        num_seconds += duration

    if num_seconds != 86400:
        msg = f"Incomplete events for {der} {mode} {day}"
        raise ValueError(msg)

    output = {
        "der": der,
        "mode": mode,
        "day": str(day),
        "min_value": min_value,
        "max_value": max_value,
    }

    # Determine time at minimum
    output["s_at_min"] = sum(
        [evt.end - evt.start for evt in mode_events if evt.value == min_value]
    )

    # Determine time at maximum
    output["s_at_max"] = sum(
        [evt.end - evt.start for evt in mode_events if evt.value == max_value]
    )

    # Determine time at break points
    breaks = sorted(tuple(breaks), reverse=True)
    for break_val in breaks:
        output[f"s_at_or_below_{break_val}"] = sum(
            [evt.end - evt.start for evt in mode_events if evt.value <= break_val]
        )
    return output


def update_daily_summaries(previous_days: int = 3):
    update_mode_events()
    today = current_date()
    start_date = today - timedelta(days=previous_days)
    records = []
    for der in get_ders():
        for mode in get_modes(der):
            for day in get_mode_event_days(der, mode):
                if day >= today:
                    continue  # Do not calculate until day is over
                if day < start_date:
                    continue  # Do not calculate historical days
                if daily_summary_exists(der, mode, day):
                    log.debug(
                        "Skip summary calculation for existing record %s %s %s",
                        der,
                        mode,
                        day,
                    )
                    continue  # Skip already calculated
                try:
                    res = get_mode_day_distribution(der, mode, day)
                except ValueError:
                    log.info("Incomplete day for %s %s %s", der, mode, day)
                    continue
                records.append(res)
    add_daily_summaries(records)


def clear_old_events(days_to_keep: float = 3.0):
    # Perform some analysis before clearing
    update_daily_summaries(int(days_to_keep))

    # Clear old events
    db_path = create_db()
    sql = "DELETE FROM events WHERE (start + duration) < :expire"
    now_utc = int(datetime.now(timezone.utc).timestamp())
    seconds_to_keep = int(days_to_keep * 86400)
    expire = now_utc - seconds_to_keep
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"expire": expire})
    db.vacuum()
