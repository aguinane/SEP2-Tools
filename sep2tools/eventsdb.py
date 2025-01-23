from datetime import datetime, timezone
from pathlib import Path

from sqlite_utils import Database

from .models import DERControl

DEFAULT_OUTPUT_DIR = Path("")


def create_db(output_dir: Path = DEFAULT_OUTPUT_DIR):
    output_path = output_dir / "events.db"
    db = Database(output_path, strict=True)
    events = db["events"]
    columns = {
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
    events.create(
        columns,
        pk="mRID",
        not_null=["creationTime", "start", "duration", "controls"],
        if_not_exists=True,
    )


def add_events(events: list[DERControl], output_dir: Path = DEFAULT_OUTPUT_DIR):
    output_path = output_dir / "events.db"
    create_db()
    db = Database(output_path)
    records = [
        {
            "mRID": evt.mRID,
            "creationTime": evt.creationTime,
            "currentStatus": evt.EventStatus.currentStatus,
            "start": evt.interval.start,
            "duration": evt.interval.duration,
            "randomizeStart": evt.randomizeStart,
            "randomizeDuration": evt.randomizeDuration,
            "controls": evt.controls,
            "program": evt.ProgramInfo.program,
            "primacy": evt.ProgramInfo.primacy,
        }
        for evt in events
    ]
    db["events"].insert_all(records, replace=True)


def clear_old_events(output_dir: Path = DEFAULT_OUTPUT_DIR, days_to_keep: float = 3.0):
    output_path = output_dir / "events.db"
    create_db()

    sql = "DELETE FROM events WHERE (start + duration) < :expire"
    now_utc = int(datetime.now(timezone.utc).timestamp())
    db = Database(output_path)
    with db.conn:
        db.execute(sql, {"expire": now_utc})
    db.vacuum()
