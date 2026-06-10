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


def create_events_db(name: str = "events.db") -> Path:
    """Create the events database if it doesn't exist."""
    db_path = EVENTS_DB_DIR / name
    if db_path.exists():
        return db_path
    db = Database(db_path, strict=True)
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
    return db_path


def query_events_db(
    sql: str, params: Iterable | None = None, db_name: str = "events.db"
) -> list[dict[str, Any]]:
    """Run a query against the events database and return results as list of dicts."""
    db_path = create_events_db(db_name)
    db = Database(db_path)
    res = list(db.query(sql, params))
    db.close()
    return res


def execute_events_db(
    sql: str, params: Iterable | None = None, db_name: str = "events.db"
):
    """Run a query against the events database and return results as list of dicts."""
    db_path = create_events_db(db_name)
    db = Database(db_path)
    with db.conn:
        db.execute(sql, params)
    db.close()


def vaccum_events_db(db_name: str = "events.db"):
    """Vacuum the events database ."""
    db_path = create_events_db(db_name)
    db = Database(db_path)
    db.vacuum()
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


def add_events(events: list[DERControl], db_name: str = "events.db"):
    """Add events to the database."""
    records = []
    for evt in events:
        records.extend(event_to_rows(evt))

    db_path = create_events_db(db_name)
    db = Database(db_path)
    db["events"].insert_all(records, replace=True)
    db.close()


def delete_event(mrid: str, db_name: str = "events.db"):
    """Remove an event from the database"""
    sql = "DELETE FROM events WHERE mRID = :mrid"
    execute_events_db(sql, {"mrid": mrid}, db_name=db_name)


def supersede_event(mrid: str, control_mode: str, db_name: str = "events.db"):
    """Update the CurrentStatus to Superseded (4)"""
    sql = (
        "UPDATE events SET currentStatus = 4 WHERE mRID = :mrid AND controlMode = :mode"
    )
    # Update the CurrentStatus to 4 (Superseded)
    execute_events_db(sql, {"mrid": mrid, "mode": control_mode}, db_name=db_name)


def get_programs(db_name: str = "events.db") -> list[str]:
    """Get list of programs that have events in the database"""
    sql = "SELECT DISTINCT programName FROM events"
    return [x["programName"] for x in query_events_db(sql, db_name=db_name)]


def get_program_modes(program: str, db_name: str = "events.db") -> list[str]:
    """Get list of control modes that have events for a given program"""
    sql = "SELECT DISTINCT controlMode FROM events WHERE programName = :prg"
    return [
        x["controlMode"]
        for x in query_events_db(sql, {"prg": program}, db_name=db_name)
    ]


def get_events(program: str, db_name: str = "events.db") -> list[DERControl]:
    """Get all events for a program"""
    sql = """SELECT * FROM events
    WHERE programName = :prg 
    ORDER BY intervalStart, creationTime
    """
    events = {}
    res = query_events_db(sql, {"prg": program}, db_name=db_name)
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


def get_mode_events(
    program: str, mode: str, db_name: str = "events.db"
) -> list[DERModeControl]:
    """Get all events for a program and control mode"""
    sql = """SELECT * FROM events
    WHERE programName = :prg AND controlMode = :mode
    AND currentStatus IN (0,1,999)
    ORDER BY intervalStart, creationTime
    """
    res = query_events_db(sql, {"prg": program, "mode": mode}, db_name=db_name)
    events = []
    for x in res:
        item = row_to_mode_event(x)
        if item.currentStatus in (2, 3, 4):
            continue  # Skip cancelled or superseded
        events.append(item)
    return events


def update_default(
    mrid: str, new_status: int, new_duration: int, db_name: str = "events.db"
):
    """Update the status and duration of a default event"""
    sql = "UPDATE events SET currentStatus = :status, intervalDuration = :duration "
    sql += "WHERE mRID = :mrid"
    execute_events_db(
        sql,
        {"mrid": mrid, "status": new_status, "duration": new_duration},
        db_name=db_name,
    )


def cleanup_defaults(db_name: str = "events.db"):
    """If a default has been superseded, update the old events"""
    log.info("Cleaning up default events")
    sql = """SELECT DISTINCT programName, mRID, intervalStart
    FROM events 
    WHERE intervalDuration = 999999999 AND currentStatus = 1
    ORDER BY programName, intervalStart DESC
    """
    programs = {}
    res = query_events_db(sql, db_name=db_name)
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
        update_default(mrid, new_status, new_duration, db_name=db_name)

        # Update the start in case there are even older defaults
        programs[program] = start


def supersede_overlapping(db_name: str = "events.db"):
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
    res = query_events_db(sql_dup, db_name=db_name)
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
            db_name=db_name,
        )
        # Ignore the first result (most recent) and supersede the rest
        for y in int_res[1:]:
            mrid = y["mRID"]
            mode = y["controlMode"]
            to_supersede.append((mrid, mode))
    log.info(f"Found {len(to_supersede)} events to supersede due to overlap")
    for mrid, mode in to_supersede:
        supersede_event(mrid, mode, db_name=db_name)


def delete_superseded(db_name: str = "events.db"):
    """Delete events that have been superseded or cancelled"""
    log.info("Deleting superseded events")
    sql = """
    SELECT * FROM events
    WHERE isDefault = 0
    AND currentStatus IN (2,3,4)
    """
    execute_events_db(sql, db_name=db_name)


def update_status(db_name: str = "events.db"):
    """Update status of events based on current time"""

    # Set all events with start + duration in the past to Completed (999)
    sql_completed = """UPDATE events
    SET currentStatus = 999
    WHERE isDefault = 0
    AND currentStatus IN (0,1)
    AND (intervalStart + intervalDuration) < strftime('%s', 'now')
    """
    execute_events_db(sql_completed, db_name=db_name)

    # Set all events that have started but not yet completed to Active (1)
    sql_active = """UPDATE events
    SET currentStatus = 1
    WHERE isDefault = 0
    AND currentStatus = 0
    AND intervalStart <= strftime('%s', 'now')
    AND (intervalStart + intervalDuration) > strftime('%s', 'now')
    """
    execute_events_db(sql_active, db_name=db_name)


def cleanup_events(db_name: str = "events.db"):
    """Run all cleanup functions"""
    create_events_db(name=db_name)
    cleanup_defaults(db_name=db_name)
    supersede_overlapping(db_name=db_name)
    delete_superseded(db_name=db_name)
    update_status(db_name=db_name)


def remove_old_events(retro_hours: float = 72.0, db_name: str = "events.db"):
    """Delete events that ended more than retro_hours ago"""

    cleanup_events(db_name=db_name)  # Run a cleanup first

    sql = """DELETE FROM events
    WHERE currentStatus NOT IN (0,1)
    AND (intervalStart + intervalDuration) < :cutoff
    """
    now = current_timestamp()
    cutoff_time = int(now - retro_hours * 3600)
    execute_events_db(sql, {"cutoff": cutoff_time}, db_name=db_name)

    vaccum_events_db(db_name=db_name)
