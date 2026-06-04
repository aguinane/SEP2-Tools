import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlite_utils import Database

from .event_models import DERControl, DERControlBase, DERModeControl

load_dotenv()
log = logging.getLogger(__name__)
events_dir = os.getenv("SEP2_EVENTS_DIR", "")
EVENTS_DB_DIR = Path(events_dir)
EVENTS_DB = EVENTS_DB_DIR / "events.db"


DEFAULT_DIST_BREAKS = (1500, 5000, 10000)


EVENT_COLS = {
    "mRID": str,
    "programName": str,
    "programPrimacy": int,
    "creationTime": int,
    "currentStatus": int,
    "isDefault": bool,
    "intervalStart": int,
    "intervalDuration": int,
    "randomizeStart": int,
    "randomizeDuration": int,
    "controlMode": str,
    "controlValue": int,
    "controlMultiplier": int,
}


def create_events_db() -> Path:
    """Create the events database if it doesn't exist."""
    if EVENTS_DB.exists():
        return EVENTS_DB
    db = Database(EVENTS_DB, strict=True)
    with db.conn:
        events = db["events"]
        events.create(
            EVENT_COLS,
            pk=("mRID", "controlMode"),
            not_null=(
                "mRID",
                "controlMode",
                "creationTime",
                "currentStatus",
                "intervalStart",
            ),
            if_not_exists=True,
        )
        events.create_index(("mRID",))
        events.create_index(("controlMode",))
        events.create_index(("programName",))
        events.create_index(("intervalStart",))
    return EVENTS_DB


def event_to_rows(evt: DERControl) -> list[dict[str, Any]]:
    """Convert an event to a list of rows for the database."""
    rows = []
    for cntrl in evt.controls:
        row = {
            "mRID": evt.mRID,
            "programName": evt.programName,
            "programPrimacy": evt.programPrimacy,
            "creationTime": evt.creationTime,
            "currentStatus": evt.currentStatus,
            "isDefault": evt.isDefault,
            "intervalStart": evt.intervalStart,
            "intervalDuration": evt.intervalDuration,
            "randomizeStart": evt.randomizeStart,
            "randomizeDuration": evt.randomizeDuration,
            "controlMode": cntrl.mode,
            "controlValue": cntrl.value,
            "controlMultiplier": cntrl.multiplier,
        }
        rows.append(row)
    return rows


def row_to_event(row: dict) -> DERControl:
    ctrl = DERControlBase(
        mode=row["controlMode"],
        value=row["controlValue"],
        multiplier=row["controlMultiplier"],
    )
    return DERControl(
        mRID=row["mRID"],
        programName=row["programName"],
        programPrimacy=row["programPrimacy"],
        creationTime=row["creationTime"],
        currentStatus=row["currentStatus"],
        isDefault=row["isDefault"],
        intervalStart=row["intervalStart"],
        intervalDuration=row["intervalDuration"],
        randomizeStart=row["randomizeStart"],
        randomizeDuration=row["randomizeDuration"],
        controls=[ctrl],
    )


def row_to_mode_event(row: dict) -> DERModeControl:
    return DERModeControl(
        mRID=row["mRID"],
        programName=row["programName"],
        programPrimacy=row["programPrimacy"],
        creationTime=row["creationTime"],
        currentStatus=row["currentStatus"],
        isDefault=row["isDefault"],
        intervalStart=row["intervalStart"],
        intervalDuration=row["intervalDuration"],
        randomizeStart=row["randomizeStart"],
        randomizeDuration=row["randomizeDuration"],
        controlMode=row["controlMode"],
        controlValue=row["controlValue"],
        controlMultiplier=row["controlMultiplier"],
    )


def add_events(events: list[DERControl]):
    """Add events to the database."""
    records = []
    for evt in events:
        records.extend(event_to_rows(evt))

    db_path = create_events_db()
    db = Database(db_path)
    with db.conn:
        db["events"].insert_all(records, replace=True)


def delete_event(mrid: str):
    """Remove an event from the database"""
    sql = "DELETE FROM events WHERE mRID = :mrid"
    db = Database(EVENTS_DB)
    with db.conn:
        db.execute(sql, {"mrid": mrid})


def supersede_event(mrid: str, control_mode: str):
    """Update the CurrentStatus to Superseded (4)"""
    sql = (
        "UPDATE events SET currentStatus = 4 WHERE mRID = :mrid AND controlMode = :mode"
    )
    # Update the CurrentStatus to 4 (Superseded)
    db = Database(EVENTS_DB)
    with db.conn:
        db.execute(sql, {"mrid": mrid, "mode": control_mode})


def get_program_modes(program: str) -> list[str]:
    sql = "SELECT DISTINCT controlMode FROM events WHERE programName = :prg"
    db_path = create_events_db()
    db = Database(db_path)
    with db.conn:
        res = db.query(sql, {"prg": program})
        return [x["controlMode"] for x in res]


def get_events(program: str) -> list[DERControl]:
    sql = """SELECT * FROM events
    WHERE programName = :prg 
    ORDER BY intervalStart, creationTime"""
    db_path = create_events_db()
    db = Database(db_path)
    events = {}
    with db.conn:
        res = db.query(sql, {"prg": program})
        for x in res:
            item = row_to_event(x)
            if item.currentStatus in (2, 3, 4):
                continue  # Skip cancelled or superseded
            mrid = item.mRID
            if mrid not in events:
                events[mrid] = item
            else:
                events[mrid].controls.append(item.controls)
    return list(events.values())


def get_mode_events(program: str, mode: str) -> list[DERModeControl]:
    sql = """SELECT * FROM events
    WHERE programName = :prg AND controlMode = :mode
    ORDER BY intervalStart, creationTime"""
    db_path = create_events_db()
    db = Database(db_path)
    events = []
    with db.conn:
        res = db.query(sql, {"prg": program, "mode": mode})
        for x in res:
            item = row_to_mode_event(x)
            if item.currentStatus in (2, 3, 4):
                continue  # Skip cancelled or superseded
            events.append(item)
    return events


def update_default(mrid: str, new_status: int, new_duration: int):
    db_path = EVENTS_DB
    sql = "UPDATE events SET currentStatus = :status, intervalDuration = :duration "
    sql += "WHERE mRID = :mrid"
    db = Database(db_path)
    with db.conn:
        db.execute(sql, {"mrid": mrid, "status": new_status, "duration": new_duration})


def cleanup_defaults():
    """If a default has been superseded, update the old events"""
    log.info("Cleaning up default events")
    sql = """SELECT DISTINCT programName, mRID, intervalStart
    FROM events 
    WHERE intervalDuration = 999999999 AND currentStatus = 1
    ORDER BY programName, intervalStart DESC
    """
    db_path = create_events_db()
    db = Database(db_path)
    programs = {}
    with db.conn:
        res = db.query(sql)
        for x in res:
            program = x["programName"]
            start = x["intervalStart"]
            if program not in programs:
                programs[program] = start
                continue  # This one is active

            # This one is old - change status and duration
            mrid = x["mRID"]
            end = programs[program] - 1
            new_duration = end - start
            new_status = 999  # Completed
            update_default(mrid, new_status, new_duration)

            # Update the start in case there are even older defaults
            programs[program] = start


def supersede_overlapping():
    """Check for events with duplicate control events for same interval"""
    log.info("Superseding overlapping events")
    sql_dup = """
    WITH overlaps AS (
    SELECT programName, controlMode, intervalStart, intervalDuration, 
        count(*) as num_events
    FROM events
    WHERE isDefault = 0
    AND currentStatus IN (0,1,999)
    GROUP BY programName, controlMode, intervalStart, intervalDuration
    )
    SELECT * FROM overlaps
    WHERE num_events > 1
    ORDER BY num_events DESC
    """
    sql_matches = """SELECT * FROM events
    WHERE programName = :prg AND controlMode = :mode 
    AND intervalStart = :start AND intervalDuration = :duration
    ORDER BY creationTime DESC
    """
    db_path = create_events_db()
    db = Database(db_path)
    to_supersede = []
    with db.conn:
        res = list(db.query(sql_dup))
        for x in res:
            program = x["programName"]
            mode = x["controlMode"]
            start = x["intervalStart"]
            duration = x["intervalDuration"]
            num_events = x["num_events"]
            if num_events <= 1:
                continue  # No duplicates, move on

            int_res = db.query(
                sql_matches,
                {"prg": program, "mode": mode, "start": start, "duration": duration},
            )
            next(int_res)
            for y in int_res:
                mrid = y["mRID"]
                mode = y["controlMode"]
                to_supersede.append((mrid, mode))
    log.info(f"Found {len(to_supersede)} events to supersede due to overlap")
    for mrid, mode in to_supersede:
        supersede_event(mrid, mode)


def delete_superseded():
    """Delete events that have been superseded or cancelled"""
    log.info("Deleting superseded events")
    sql = """
    SELECT * FROM events
    WHERE isDefault = 0
    AND currentStatus IN (2,3,4)
    """
    db_path = create_events_db()
    db = Database(db_path)
    with db.conn:
        db.execute(sql)
