from datetime import datetime
from io import StringIO
import logging
import os
from threading import Thread, current_thread, get_ident
from typing import Optional, Protocol, runtime_checkable
import pandas as pd

from components.containers import Report


logger_main = logging.getLogger(__name__)

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



class FileSaveHandler(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue


    def _read_stream(self, report: Report) -> None:
        
        logger_main.debug('Reading content of %s', report.name)
        df = pd.read_csv(StringIO(report.response),   
                                    dtype='string',
                                    low_memory=False)

        logger_main.debug('Removing last 5 lines, footer of %s', report.name)
        report.content = df.head(df.shape[0] -5)

        return None
    
    def _save_to_csv(self, report: Report) -> None:

        file_path = f'{"/".join([str(report.path), report.name])}.csv'
        logger_main.debug('Parsing path for %s -> %s', report.name, file_path)

        logger_main.debug('%s is saving file for %s -> %s', current_thread().name, report.name, file_path)
        report.content.to_csv(file_path,
                            index=False)
        
        logger_main.debug('%s saved %s -> %s', current_thread().name, report.name, file_path)
        report.downloaded = True
        
        report.pull_date = datetime.now()
        report.size = round((os.stat(file_path).st_size / (1024 * 1024)),1)
        report.processing_time = report.pull_date - report.created_date

        logger_main.debug('%s succesfully saved by %s at report.pull_date, operation took: %s, file size: %s', 
                          report.name, current_thread().name, report.processing_time, report.size)
        
        return None    

    def _erase_report(self, report: Report) -> None:
        
        logger_main.debug('Deleting response and content for %s', report.name)
        report.response = ""
        report.content = pd.DataFrame()

        return None    
    
    def report_processing(self, report: Report) -> None:
        
        if report.valid:
            try:
                self._read_stream(report)
                self._save_to_csv(report)
                self._erase_report(report)
                
            except pd.errors.EmptyDataError as e:
                logger_main.warning('%s timeouted, attmpts: %s',report.name, report.attempt_count)
                report.downloaded = False
            
            except pd.errors.ParserError as e:
                logger_main.warning('%s unexpected end of stream: %s',report.name, report.attempt_count)
                report.downloaded = False
        else:
            report.downloaded = True
        return None

    def run(self):
        
        logger_main.debug('%s starting', current_thread().name)
        while True:
            report = self.queue.get()
            if report:
                
                logger_main.debug('%s processing %s', current_thread().name, report.name)
                try:
                    report.id
                    self.report_processing(report)
                finally:
                    logger_main.debug('%s finishing %s', current_thread().name, report.name)
                    self.queue.task_done()
