import os
import logging
import pandas as pd

from queue import Queue
from pathlib import Path
from datetime import datetime
from io import StringIO
from threading import Thread, current_thread, active_count
from typing import NoReturn, Protocol, runtime_checkable

from components.containers import ReportProtocol


logger_main = logging.getLogger(__name__)


@runtime_checkable
class WorkerFactoryProtocol(Protocol):
    """Protocol class for worker factory objects.

    :param queue: Shared, thread-safe queue.
    :type queue: Queue
    :param threads: Number of threads, equal to number of Workers to be deployed.
    :type threads: int
    """

    queue: Queue
    threads: int

    def create_workers(self) -> None:
        """Creates workers on independent threads
        """
        ...

    @staticmethod
    def active_workers() -> int:
        """Counts active works in current time.

        :return: Number of active workers.
        :rtype: int
        """
        ...


@runtime_checkable
class WorkerProtocol(Protocol):
    """Protocol class for worker factory objects.

    :param queue: Shared, thread-safe queue.
    :type queue: Queue
    """

    def _read_stream(self, report: ReportProtocol) -> None:
        """Reads the stream of data kept in Report object via Pandas read method. Deletes response content from the object.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """
        ...

    def _save_to_csv(self, report: ReportProtocol) -> None:
        """Saves readed data to CSV file using Pandas save method.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """
        ...

    def _erase_report(self, report: ReportProtocol) -> None:
        """Erases the report data.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """
        ...

    def report_processing(self, report: ReportProtocol) -> None:
        """Orchiestrates the report processing.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """
        ...

    def run(self) -> NoReturn:
        """Starts listner process on sepearet thread, awaits objects in the queue.

        :return: Method never returns.
        :rtype: NoReturn
        """
        ...


class WorkerFactory:
    """Concrete class representing WorkerFactory object.
    """

    def __init__(self,
                 queue: Queue,
                 *,
                 threads: int = 1):
        """Constructor method for WorkerFactory, automatically creates and deploys workers after initialization.

        :param queue: Shared, thread-safe queue.
        :type queue: Queue
        :param threads: Number of threads, equal to number of Workers to be deployed. Defaults to 1.
        :type threads: int
        """

        self.queue: Queue = queue
        self.threads: int = threads

        self.create_workers()

    def create_workers(self) -> None:
        """Deploys given number of workers.
        """

        for num in range(self.threads):
            worker = Worker(self.queue)
            worker.name = f'Slave-{num}'
            worker.daemon = True
            worker.start()

        return None

    @staticmethod
    def active_workers() -> int:
        """Returns number of currently active workers.

        :return: Number of workers.
        :rtype: int
        """
        return active_count() - 1


class Worker(Thread):
    """Concrete class representing Worker object.
    """

    def __init__(self, queue: Queue):
        """Constructor method for Worker.

        :param queue: Shared, thread-safe queue.
        :type queue: Queue
        """

        Thread.__init__(self)
        self.queue = queue

    def _read_stream(self, report: ReportProtocol) -> None:
        """Reads report's response and save it as `content` atribute. Erases saved response. 

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """

        logger_main.debug('Reading content of %s', report.name)

        try:
            report.content = pd.read_csv(StringIO(report.response),
                                         dtype='string',
                                         low_memory=False)
        except pd.errors.EmptyDataError as e:
            logger_main.warning('%s timeouted, attmpts: %s',
                                report.name, report.attempt_count)
            report.downloaded = False
        finally:
            report.response = ''
            logger_main.debug(
                'Removing last 5 lines, footer of %s', report.name)
            report.content = report.content.head(report.content.shape[0] - 5)

        return None

    def _parse_save_path(self, report: ReportProtocol) -> os.PathLike:
        """Parses path to save location.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        :return: Path to save location
        :rtype: os.PathLike
        """
        return Path(f'{"/".join([str(report.path), report.name])}.csv')

    def _save_to_csv(self, report: ReportProtocol) -> None:
        """Saves report content to CSV file. Sets object flags.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """

        file_path = self._parse_save_path(report)

        logger_main.debug('Parsing path for %s -> %s', report.name, file_path)

        logger_main.debug('%s is saving file for %s -> %s',
                          current_thread().name, report.name, file_path)

        try:
            report.content.to_csv(file_path,
                                  index=False)
        except pd.errors.ParserError as e:
            logger_main.warning('%s unexpected end of stream: %s',
                                report.name, report.attempt_count)
            report.downloaded = False
        finally:
            logger_main.debug('%s saved %s -> %s',
                              current_thread().name, report.name, file_path)
            report.downloaded = True

            report.pull_date = datetime.now()
            report.size = round(
                (os.stat(file_path).st_size / (1024 * 1024)), 1)
            report.processing_time = report.pull_date - report.created_date

            logger_main.debug('%s succesfully saved by %s at %s, operation took: %s, file size: %s',
                              report.name, current_thread().name, report.pull_date, report.processing_time, report.size)

        return None

    def _erase_report(self, report: ReportProtocol) -> None:
        """Deletes report content in ReportProtocol object.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """

        logger_main.debug('Deleting response and content for %s', report.name)
        report.content = pd.DataFrame()

        return None

    def process_report(self, report: ReportProtocol) -> None:
        """Orchiestrates entire process of downloading the report.

        :param report: Instance of the ReportProtocol object.
        :type report: ReportProtocol
        """

        if report.valid:
            self._read_stream(report)
            self._save_to_csv(report)
            self._erase_report(report)
        else:
            report.downloaded = True
        return None

    def run(self) -> NoReturn:
        """begins to listen to the queue. Starts processing once will get item from the queue. Sends signal to the queue once task is done.

        :return: Function never returns.
        :rtype: NoReturn
        """

        logger_main.debug('%s starting', current_thread().name)
        while True:
            report = self.queue.get()

            if report:
                logger_main.debug('%s processing %s',
                                  current_thread().name, report.name)
                try:
                    self.process_report(report)
                except Exception as e:
                    logger_main.debug(
                        '%s failed while processing %s -> %s', current_thread().name, report.name, e)
                finally:
                    logger_main.debug('%s finishing %s',
                                      current_thread().name, report.name)
                    self.queue.task_done()
