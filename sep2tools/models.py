from enum import IntEnum

from pydantic import BaseModel


class CurrentStatus(IntEnum):
    Scheduled = 0
    Active = 1
    Cancelled = 2
    CancelledWithRandomization = 3
    Superseded = 4


class Status(IntEnum):
    EventReceived = 1
    EventStarted = 2
    EventCompleted = 3
    Superseded = 4
    EventCancelled = 6
    EventSuperseded = 7


class EventStatus(BaseModel):
    currentStatus: CurrentStatus
    dateTime: int = 0


class DateTimeInterval(BaseModel):
    start: int
    duration: int


class DERControlBase(BaseModel):
    mode: str
    value: int
    multiplier: int = 0


class ProgramInfo(BaseModel):
    program: str = ""
    primacy: int


class DERControl(BaseModel):
    mRID: str
    creationTime: int
    EventStatus: EventStatus
    interval: DateTimeInterval
    randomizeStart: int = 0
    randomizeDuration: int = 0
    controls: list[DERControlBase]
    ProgramInfo: ProgramInfo


class ModeEvent(BaseModel):
    mrid: str
    primacy: int
    creation_time: int
    start: int
    end: int
    value: int
    rand_start: int
    rand_dur: int
