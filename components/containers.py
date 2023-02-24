import csv
import logging

from dataclasses import dataclass, field
from os import PathLike
from typing import Any, Generator, Protocol, runtime_checkable
from datetime import datetime, timedelta
from pandas import DataFrame


logger_main = logging.getLogger(__name__)


@runtime_checkable
class ReportProtocol(Protocol):
    """
    Protocol class for report object.

    :param type: Report type, allowed options ['SFDC'], type drives connector and report objects selection
    :type type: str
    :param name: Report name, propagated to report file name
    :type name: str
    :param id: Report id, identification number of the report in SFDC
    :type id: str
    :param path: Report path, save location for the report in form of Path object
    :type path: PathLike
    :param export_params: Default parameters required by SFDC. Defaults to '?export=csv&enc=UTF-8&isdtp=p1'.
    :type export_params: str
    :param downloaded: Flag indicating whether the reports has been succesfully downloaded or not
    :type downloaded: bool
    :param valid: Flag indicating whether the response has been succesfully retrieved or not
    :type valid: bool
    :param created_date: Report save completition date
    :type created_date: datetime
    :param pull_date: Report response completition date
    :type pull_date: datetime
    :param processing_time: The time it took to process the report in seconds 
    :type pull_date: timedelta
    :param attempt_count: Number of attempts to process the report 
    :type attempt_count: int
    :param size: Size of saved report file in Mb
    :type size: float
    :param response: Container for request response
    :type response: str
    :param content: Pandas DataFrame based on response
    :type content: DataFrame
    """

    type: str
    name: str
    id: str
    path: PathLike
    export_params: str
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
class ReportsContainerProtocol(Protocol):
    """Protocol class for report container object.

    :param report_params_list: Collection of dicts with parameters for object crafting.
    :type report_params_list: list[dict[str, Any]]
    :param summary_report_path: Path to save location of summary report.
    :type summary_report_path: PathLike
    """

    def create_reports(self) -> list[ReportProtocol]:
        """Orchestrating method to handle report objects factory

        :return: Collection of Reports
        :rtype: list[ReportProtocol]
        """
        ...

    def create_summary_report(self) -> None:
        """Creates summary report which consist of all important details regarding Report objects. 
        Summary report is generated once all the reports are completed.
        """
        ...


@dataclass(slots=True)
class SfdcReport():
    """Concrete class representing Report object from SFDC.

    :param type: Report type, allowed options ['SFDC'], type drives connector and report objects selection
    :type type: str
    :param name: Report name, propagated to report file name
    :type name: str
    :param id: Report id, identification number of the report in SFDC
    :type id: str
    :param path: Report path, save location for the report in form of Path object
    :type path: PathLike
    :param export_params: Default parameters required by SFDC. Defaults to '?export=csv&enc=UTF-8&isdtp=p1'.
    :type export_params: str
    :param downloaded: Flag indicating whether the reports has been succesfully downloaded or not. Defaults to False.
    :type downloaded: bool
    :param valid: Flag indicating whether the response has been succesfully retrieved or not. Defaults to False.
    :type valid: bool
    :param created_date: Report save completition date. Defaults to current datetime.
    :type created_date: datetime
    :param pull_date: Report response completition date. Defaults to current datetime.
    :type pull_date: datetime
    :param processing_time: The time it took to process the report in seconds. Defaults to 0 microseconds.
    :type pull_date: timedelta
    :param attempt_count: Number of attempts to process the report. Defaults to 0 .
    :type attempt_count: int
    :param size: Size of saved report file in Mb. Defaults to 0.0 .
    :type size: float
    :param response: Container for request response. Defaults to empty string.
    :type response: str
    :param content: Pandas DataFrame based on response. Defaults to empty Pandas DataFrame.
    :type content: DataFrame
    """

    type: str
    name: str
    id: str
    path: PathLike
    export_params: str = '?export=csv&enc=UTF-8&isdtp=p1'
    downloaded: bool = False
    valid: bool = False
    created_date: datetime = datetime.now()
    pull_date: datetime = datetime.now()
    processing_time: timedelta = timedelta(microseconds=0)
    attempt_count: int = 0
    size: float = 0.0
    response: str = ""
    content: DataFrame = field(default_factory=DataFrame)


class ReportsContainer():
    """Concrete class representing ReportContainer object. 
    """

    def __init__(self,
                 reports_params_list: list[dict[str, Any]],
                 summary_report_path: PathLike):
        """Constructor method for ReportContainer, automatically creates reports after initialization
        """

        self.reports_params_list: list[dict[str, Any]] = reports_params_list
        self.summary_report_path: PathLike = summary_report_path
        self.reports_list: list[ReportProtocol]

        self.create_reports()

    def _create_sfdc_reports(self) -> Generator[SfdcReport, None, None]:
        """SFDC Report objects factory

        :return: Generator with SFDC Reeport objects
        :rtype: Generator[SfdcReport, None, None]
        :yield: SFDC Report instance based on parsed report parameters
        :rtype: SfdcReport
        """

        logger_main.debug("Creating SFDC report objects")
        reports = (SfdcReport(**dict) for dict in self.reports_params_list)

        return reports

    def create_reports(self) -> list[ReportProtocol]:
        """Orchestrating method to handle report objects factory

        :return: Collection of Reports
        :rtype: list[SfdcReport]
        """

        logger_main.debug("Creating all report objects")
        self.reports_list = list(self._create_sfdc_reports())

        return self.reports_list

    def create_summary_report(self) -> None:
        """Creates summary report which consist of all important details regarding reports. 
        Report is generated once all the reports are completed.
        """

        logger_main.debug("Creating summary report, saved in %s",
                          self.summary_report_path)

        header = ['file_name', 'report_id', 'type', 'valid', 'created_date',
                  'pull_date', 'processing_time', 'attempt_count', 'file_size']

        with open(self.summary_report_path, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(header)

            for report in self.reports_list:
                writer.writerow([report.name, report.id, report.type, report.valid, report.created_date,
                                report.pull_date, report.processing_time, report.attempt_count, report.size])

        return None
