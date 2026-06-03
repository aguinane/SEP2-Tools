from enum import IntEnum

from pydantic import BaseModel


class CurrentStatus(IntEnum):
    Scheduled = 0
    Active = 1
    Cancelled = 2
    CancelledWithRandomization = 3
    Superseded = 4
    Completed = 999


class DERControlBase(BaseModel):
    mode: str
    value: int
    multiplier: int = 0


class DERControl(BaseModel):
    mRID: str
    programName: str = ""
    programPrimacy: int = 0
    creationTime: int
    currentStatus: CurrentStatus
    statusTime: int = 0
    isDefault: bool = False
    intervalStart: int
    intervalDuration: int = 0
    randomizeStart: int = 0
    randomizeDuration: int = 0
    controls: list[DERControlBase] = []


class DERModeControl(BaseModel):
    mRID: str
    programName: str = ""
    programPrimacy: int = 0
    creationTime: int
    currentStatus: CurrentStatus
    statusTime: int = 0
    isDefault: bool = False
    intervalStart: int
    intervalDuration: int = 0
    randomizeStart: int = 0
    randomizeDuration: int = 0
    controlMode: str
    controlValue: int
    controlMultiplier: int = 0
