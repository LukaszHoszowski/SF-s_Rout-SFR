import os
import logging
import pandas as pd

from asyncio import Queue
from datetime import datetime
from io import StringIO
from threading import Thread, current_thread, active_count
from typing import NoReturn, Optional, Protocol, runtime_checkable

from components.containers import ReportProt


logger_main = logging.getLogger(__name__)

@runtime_checkable
class WorkerFactoryProt(Protocol):
    """
    A Protocol class as a scaffold for worker factory.
    
    ...
    Attributes
    ----------
    queue: Queue
        shared queue for items
    cli_threads: int
        number of threads from cli parameters
    cli_report: str
        single report mode from cli parameters
    _workers_count: int
        calculated number of workers to be deployed
        
    Methods
    ----------    
    create_workers() -> None:
        Creates workers
    
    active_workers() -> int:
        Returns number of active workers
    """
    
    queue: Queue
    cli_threads: int
    cli_report: str
    _workers_count: str
 
    def create_workers(self) -> None:
        ...
        
    @staticmethod
    def active_workers() -> int:
        ...

@runtime_checkable
class FileHandlerProt(Protocol):
    """
    A Protocol class as a scaffold for file handler.
    
    ...
    Attributes
    ----------
    queue: Queue
        shared queue for items

    Methods
    ----------    
    _read_stream() -> None:
        Reads the stream of data kept in Report object via Pandas read method. Deletes response content from the object.
    
    _save_to_csv() -> None:
        Saves readed data to CSV file using Pandas save method.

    _erase_report() -> None:
        Erases the report data.

    report_processing() -> None:
        Orchiestrates the report processing.

    run() -> None
        Starts thread listener process.
    """
    
    reports: list[Optional[ReportProt]] 
    
    def _read_stream(self, report: ReportProt) -> None:
        ...
        
    def _save_to_csv(self, report: ReportProt) -> None:
        ...

    def _erase_report(self, report: ReportProt) -> None:
        ...
    
    def report_processing(self, report: ReportProt) -> None:
        ...

    def run(self) -> NoReturn:
        ...

class WorkerFactory:

    def __init__(self, queue, cli_threads, cli_report):
        self.queue = queue
        self.cli_threads = cli_threads
        self.cli_report = cli_report
        self._workers_count = (int((os.cpu_count() or 4) / 2) if not cli_threads else cli_threads) if not self.cli_report else 1
        self.create_workers()

    def create_workers(self) -> None:
        for num in range(self._workers_count):
            worker = FileHandler(self.queue)
            worker.name = f'Slave-{num}'
            worker.daemon = True
            worker.start()

        return None
    
    @staticmethod
    def active_workers() -> int:
        return active_count() - 1

class FileHandler(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def _read_stream(self, report: ReportProt) -> None:
        
        logger_main.debug('Reading content of %s', report.name)
        
        try:
            report.content = pd.read_csv(StringIO(report.response),   
                                        dtype='string',
                                        low_memory=False)
        except pd.errors.EmptyDataError as e:
            logger_main.warning('%s timeouted, attmpts: %s',report.name, report.attempt_count)
            report.downloaded = False
        finally:
            report.response = ''
            logger_main.debug('Removing last 5 lines, footer of %s', report.name)
            report.content = report.content.head(report.content.shape[0] -5)

        return None
    
    def _save_to_csv(self, report: ReportProt) -> None:

        file_path = f'{"/".join([str(report.path), report.name])}.csv'
        logger_main.debug('Parsing path for %s -> %s', report.name, file_path)

        logger_main.debug('%s is saving file for %s -> %s', current_thread().name, report.name, file_path)
        
        try:
            report.content.to_csv(file_path,
                                index=False)
        except pd.errors.ParserError as e:
                logger_main.warning('%s unexpected end of stream: %s',report.name, report.attempt_count)
                report.downloaded = False    
        finally:
            logger_main.debug('%s saved %s -> %s', current_thread().name, report.name, file_path)
            report.downloaded = True
            
            report.pull_date = datetime.now()
            report.size = round((os.stat(file_path).st_size / (1024 * 1024)),1)
            report.processing_time = report.pull_date - report.created_date

            logger_main.debug('%s succesfully saved by %s at %s, operation took: %s, file size: %s', 
                            report.name, current_thread().name, report.pull_date, report.processing_time, report.size)
            
        return None    

    def _erase_report(self, report: ReportProt) -> None:
        
        logger_main.debug('Deleting response and content for %s', report.name)
        report.content = pd.DataFrame()

        return None    
    
    def report_processing(self, report: ReportProt) -> None:
        
        if report.valid:
            self._read_stream(report)
            self._save_to_csv(report)
            self._erase_report(report)
        else:
            report.downloaded = True
        return None

    def run(self) -> NoReturn:
        
        logger_main.debug('%s starting', current_thread().name)
        while True:
            report = self.queue.get()
            if report:
                
                logger_main.debug('%s processing %s', current_thread().name, report.name)
                try:
                    report.id
                    self.report_processing(report)
                except Exception as e:
                    logger_main.debug('%s failed while processing %s -> %s' , current_thread().name, report.name, e)
                finally:
                    logger_main.debug('%s finishing %s', current_thread().name, report.name)
                    self.queue.task_done()
