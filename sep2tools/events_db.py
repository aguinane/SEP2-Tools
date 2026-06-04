import logging
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlite_utils import Database

from .event_models import DERControl, DERControlBase, DERModeControl
from .times import current_timestamp

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
    db.close()
    return EVENTS_DB


def query_events_db(sql: str, params: Iterable | None = None) -> list[dict[str, Any]]:
    """Run a query against the events database and return results as list of dicts."""
    db_path = create_events_db()
    db = Database(db_path)
    res = list(db.query(sql, params))
    db.close()
    return res


def execute_events_db(sql: str, params: Iterable | None = None):
    """Run a query against the events database and return results as list of dicts."""
    db_path = create_events_db()
    db = Database(db_path)
    with db.conn:
        db.execute(sql, params)
    db.close()


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
    db["events"].insert_all(records, replace=True)
    db.close()


def delete_event(mrid: str):
    """Remove an event from the database"""
    sql = "DELETE FROM events WHERE mRID = :mrid"
    execute_events_db(sql, {"mrid": mrid})


def supersede_event(mrid: str, control_mode: str):
    """Update the CurrentStatus to Superseded (4)"""
    sql = (
        "UPDATE events SET currentStatus = 4 WHERE mRID = :mrid AND controlMode = :mode"
    )
    # Update the CurrentStatus to 4 (Superseded)
    execute_events_db(sql, {"mrid": mrid, "mode": control_mode})


def get_program_modes(program: str) -> list[str]:
    sql = "SELECT DISTINCT controlMode FROM events WHERE programName = :prg"
    return [x["controlMode"] for x in query_events_db(sql, {"prg": program})]


def get_events(program: str) -> list[DERControl]:
    sql = """SELECT * FROM events
    WHERE programName = :prg 
    ORDER BY intervalStart, creationTime"""
    events = {}
    res = query_events_db(sql, {"prg": program})
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
    AND currentStatus IN (0,1,999)
    ORDER BY intervalStart, creationTime
    """
    res = query_events_db(sql, {"prg": program, "mode": mode})
    events = []
    for x in res:
        item = row_to_mode_event(x)
        if item.currentStatus in (2, 3, 4):
            continue  # Skip cancelled or superseded
        events.append(item)
    return events


def update_default(mrid: str, new_status: int, new_duration: int):
    sql = "UPDATE events SET currentStatus = :status, intervalDuration = :duration "
    sql += "WHERE mRID = :mrid"
    execute_events_db(
        sql, {"mrid": mrid, "status": new_status, "duration": new_duration}
    )


def cleanup_defaults():
    """If a default has been superseded, update the old events"""
    log.info("Cleaning up default events")
    sql = """SELECT DISTINCT programName, mRID, intervalStart
    FROM events 
    WHERE intervalDuration = 999999999 AND currentStatus = 1
    ORDER BY programName, intervalStart DESC
    """
    programs = {}
    res = query_events_db(sql)
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
    to_supersede = []
    res = query_events_db(sql_dup)
    for x in res:
        program = x["programName"]
        mode = x["controlMode"]
        start = x["intervalStart"]
        duration = x["intervalDuration"]
        num_events = x["num_events"]
        if num_events <= 1:
            continue  # No duplicates, move on

        int_res = query_events_db(
            sql_matches,
            {"prg": program, "mode": mode, "start": start, "duration": duration},
        )
        # Ignore the first result (most recent) and supersede the rest
        for y in int_res[1:]:
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
    execute_events_db(sql)


def update_status():
    """Update status of events based on current time"""

    # Set all events with start + duration in the past to Completed (999)
    sql_completed = """UPDATE events
    SET currentStatus = 999
    WHERE isDefault = 0
    AND currentStatus IN (0,1)
    AND (intervalStart + intervalDuration) < strftime('%s', 'now')
    """
    execute_events_db(sql_completed)

    # Set all events that have started but not yet completed to Active (1)
    sql_active = """UPDATE events
    SET currentStatus = 1
    WHERE isDefault = 0
    AND currentStatus = 0
    AND intervalStart <= strftime('%s', 'now')
    AND (intervalStart + intervalDuration) > strftime('%s', 'now')
    """
    execute_events_db(sql_active)


def cleanup_events():
    """Run all cleanup functions"""
    create_events_db()
    cleanup_defaults()
    supersede_overlapping()
    delete_superseded()
    update_status()


def remove_old_events(retro_hours: float = 72.0):
    """Delete events that ended more than retro_hours ago"""

    cleanup_events()  # Run a cleanup first

    sql = """DELETE FROM events
    WHERE currentStatus NOT IN (0,1)
    AND (intervalStart + intervalDuration) < :cutoff
    """
    now = current_timestamp()
    cutoff_time = int(now - retro_hours * 3600)
    execute_events_db(sql, {"cutoff": cutoff_time})
