import csv
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Generator, Optional, Protocol, runtime_checkable
from datetime import datetime, timedelta

from pandas import DataFrame

logger_main = logging.getLogger(__name__)

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

    type: str 
    name: str
    id: str
    path: Path
    params: str
    downloaded: bool
    valid: bool
    created_date: datetime
    pull_date: datetime
    processing_time: timedelta
    attempt_count: int
    size: float
    response: str
    content: DataFrame

@runtime_checkable
class Container(Protocol):
    """
    A Protocol class as a scaffold for report objects.
    
    ...
    
    Attributes
    ----------
    report_id: str
        report id from the system
    """

    report_list: list[dict[str, str]]

    def create_reports(self) -> list[Report]:
        ...

@dataclass(slots=True)
class SfdcReport():

    type: str 
    name: str
    id: str
    path: Path
    params: str = ''
    downloaded: bool = False
    valid: bool = False
    created_date: datetime = datetime.now()
    pull_date: datetime = datetime.now()
    processing_time: timedelta = timedelta(microseconds=0)
    attempt_count: int = 0
    size: float = 0.0
    response: str = ""
    content: DataFrame = field(default_factory=DataFrame)


class ReportContainer():
    def __init__(self, 
                report_list_path: Path,
                summary_report_path: Path,
                cli_report: str,
                report_params: list[dict]=[dict()], 
                report_list: list=[]):
        
        self.report_list_path = report_list_path
        self.summary_report_path = summary_report_path
        self.cli_report = cli_report.split(',') if cli_report else []
        self.report_params = report_params
        self.report_list = report_list
        
        
    def _parse_input_report_csv(self) -> list[dict]:
        
        logger_main.debug("Parsing input reports")
        keys = ['type', 'name', 'id', 'path', 'params']

        if self.cli_report:
            if len(self.cli_report) != 5:
                self.cli_report.append('')
            
            self.report_params = [dict(zip(keys, self.cli_report))]
        else:
            with open(self.report_list_path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                next(csv_reader)
                
                self.report_params = [dict(zip(keys, values)) for values in csv_reader]
                
        logger_main.debug("Input reports successfully generated")

        return self.report_params

    def _create_sfdc_reports(self) -> Generator:
        
        reports = (SfdcReport(**kwargs) for kwargs in self._parse_input_report_csv())

        return reports
    
    def create_reports(self) -> list[Report]:
        
        self.report_list = list(self._create_sfdc_reports())

        return self.report_list
    
    def create_summary_report(self) -> None:
        logger_main.debug("Creating summary report, saved in %s", self.summary_report_path)
        
        header = ['file_name', 'report_id', 'type', 'valid', 'created_date', 'pull_date', 'processing_time', 'attempt_count', 'file_size'] 
        
        with open(self.summary_report_path, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(header)

            for report in self.report_list:
                writer.writerow([report.name, report.id, report.type, report.valid, report.created_date, 
                                report.pull_date, report.processing_time, report.attempt_count, report.size])
        
        return None
    