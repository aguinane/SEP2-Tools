import json
from datetime import datetime, timezone
from pathlib import Path

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

DEFAULT_EVENTS_DB_DIR = Path("")
EVENTS_DB_DIR = DEFAULT_EVENTS_DB_DIR
EVENTS_DB = EVENTS_DB_DIR / "events.db"
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

    return EVENTS_DB


def add_enrolment(der: str, program: str):
    db_path = create_db()
    item = {"der": der, "program": program}
    db = Database(db_path)
    db["enrolments"].insert(item, replace=True)


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
    update_old_default_events()  # Should reduce conflicts
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


def delete_event(mrid: str):
    db_path = EVENTS_DB
    sql = "DELETE FROM events WHERE mRID = :mrid"
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"mrid": mrid})
    db.vacuum()


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


def clear_old_events(days_to_keep: float = 3.0):
    db_path = create_db()
    sql = "DELETE FROM events WHERE (start + duration) < :expire"
    now_utc = int(datetime.now(timezone.utc).timestamp())
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"expire": now_utc})
    db.vacuum()
