from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from datetime import datetime, timedelta


@runtime_checkable
class Report(Protocol):
    """
    A Protocol class as a scaffold for report objects.
    
    ...
    
    Attributes
    ----------
    report_id: str
        report id from the system
    file_name: str
        file name of the report also used as name of the report
    type: str
        type of the report, usually system name
    path: str
        folder absolute path
    downloaded: bool
        True/False flag indicating whether the report has been downloaded successfully or not
    valid: bool
        True/False flag indicating whether the report has been pulled successfully or not
    created_date: datetime.datetime
        date of creation of the report
    attempt_count: int
        how many time bot was trying to request the report
    """

    report_id: str
    file_name: str
    type: str
    path: str|None
    downloaded: bool
    valid: bool
    created_date: datetime
    pull_date: datetime
    processing_time: timedelta
    attempt_count: int
    file_size: float
    content: str

@dataclass(slots=True)
class SfdcReport():

    report_id: str
    file_name: str
    type: str = "SFDC"
    path: str|None = None
    downloaded: bool = False
    valid: bool = False
    created_date: datetime = datetime.now()
    pull_date: datetime = datetime.now()
    processing_time: timedelta = timedelta(microseconds=0)
    attempt_count: int = 0
    file_size: float = 0.0
    content: str = ""
    