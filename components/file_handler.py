import csv
from datetime import datetime
import os
from typing import Optional, Protocol, runtime_checkable

from components.containers import Report


@runtime_checkable
class SaveHandler(Protocol):
    """
    A Protocol class as a scaffold for save file handler.
    
    ...
    
    Attributes
    ----------
    sid: str
        session id
    domain: str
        system domain address
    timeout: int
        request timeout in seconds
    headers: dict
        system required headers
    export_params: str
        additional export parameters
    report: str
        report container

    Attributes
    ----------    
    send_request():
        ...
    
    def download(path: str)
    """
    
    reports: list[Optional[Report]] 
    
    def save_to_csv(self, report: Report) -> str:
        ...
        
    def final_report(self, final_report_path):
        ...


class FileSaveHandler():

    def __init__(self, reports):
        self.reports = reports
    
    def _save_to_csv(self, report: Report) -> None:
    
        file_path = f'{"/".join([str(report.path), report.file_name])}.csv'

        with open(file_path, 'w', encoding='UTF-8') as file:
            writer = csv.writer(file, quotechar='\'', escapechar='\\', doublequote=False, skipinitialspace=True, quoting=csv.QUOTE_MINIMAL) 
            
            for line in report.content.split('\n')[:-7]:
                writer.writerow([line])

        report.downloaded = True
        report.pull_date = datetime.now()
        
        fsize = round((os.stat(file_path).st_size / (1024 * 1024)),1)
        report.file_size = fsize

        report.processing_time = report.pull_date - report.created_date

        print('|', end='', flush=True)

        return None

    def _erase_report(self, report: Report) -> None:
        report.content = ""

        return None    
    
    def _report_processing(self, report: Report) -> None:
        while not report.valid:
            self._save_to_csv(report)
            self._erase_report(report)
            
        return None
    
    def summary_report(self, final_report_path: str) -> None:
        header = ['file_name', 'report_id', 'type', 'valid', 'created_date', 'pull_date', 'processing_time', 'attempt_count', 'file_size'] 
        
        with open(str(final_report_path), 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(header)

            for report in self.reports:
                writer.writerow([report.file_name, report.report_id, report.type, report.valid, report.created_date, 
                                report.pull_date, report.processing_time, report.attempt_count, report.file_size])
        
        return None