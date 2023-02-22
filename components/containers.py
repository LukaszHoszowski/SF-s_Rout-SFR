import csv
import logging

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Protocol, runtime_checkable
from datetime import datetime, timedelta
from pandas import DataFrame


logger_main = logging.getLogger(__name__)

@runtime_checkable
class ReportProt(Protocol):
    """
    Protocol class for report object.
    
    :param type: Report type, allowed options ['SFDC'], type drives connector and report objects selection
    :type type: str
    :param name: Report name, propagated to report file name
    :type name: str
    :param id: Report id, identification number of the report in SFDC
    :type id: str
    :param path: Report path, save location for the report in form of Path object
    :type path: Path
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
    path: Path
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
class ReportsContainerProt(Protocol):
    """
    A Protocol class as a scaffold for report objects.
    
    ...
    
    Attributes
    ----------
    report_id: str
        report id from the system
    """

    report_list: list[dict[str, str]]

    def create_reports(self) -> list[ReportProt]:
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


class ReportsContainer():
    def __init__(self, 
                report_list_path: Path,
                summary_report_path: Path,
                cli_report: str,
                cli_path: str):
        
        """Constructor method, automatically create reports after initialization
        """

        self.report_list_path = report_list_path
        self.summary_report_path = summary_report_path
        self.cli_report = cli_report.split(',') if cli_report else []
        self.cli_path = cli_path
        self.report_params: list[dict[str, Any]] | None = None
        self.keys = ['type', 'name', 'id', 'path', 'params']
        
        self.create_reports()

    def _input_report_path_cast(self, object_kwargs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Casts value of `path` key into Path object. 
        
        :param object_kwargs: Colection of object parameters
        :type object_kwargs: list[dict[str, Any]]
        :return: Collection of object parameters with `path` casted to Path object 
        :rtype: list[dict[str, Any]]
        """

        logger_main.debug("Parsing input reports - casting 'path' to Path object")
        
        [dict.update({'path': Path(dict['path'])}) for dict in object_kwargs]
        #TODO map(lambda dict: Path(dict['path']), object_kwargs)

        return object_kwargs

    def _input_report_single_mode_override(self) -> list[dict[str, str]]:
        """Reads parameters taken from CLI. Returns parsed parameters into object kwargs. 
        
        :return: collection of single object kwargs (parameters) based on CLI argument
        :rtype: list[dict[str, str]]
        """
        
        logger_main.debug("Parsing input reports - single mode report")
        
        if len(self.cli_report) != 5:
            logger_main.debug("Parsing input reports - single mode report | optional_params not present")
            self.cli_report.append('')
            
        return [dict(zip(self.keys, self.cli_report))]

    def _input_report_csv_standard_file_mode(self) -> list[dict[str, str]]:
        """Reads parameteres taken from input CSV. Returns parsed parameters into objects kwargs.
        
        :return: collection of objects kwargs (parameters) based on input CSV
        :rtype: list[dict[str, str]]
        """

        logger_main.debug("Parsing input reports - standard csv mode report")
        with open(self.report_list_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            logger_main.debug("Parsing input reports - standard csv mode report - skipping header")
            next(csv_reader)
            
            return [dict(zip(self.keys, values)) for values in csv_reader]
        
    def _input_report_path_override(self, object_kwargs: list[dict[str, str]]) -> list[dict[str, str]]:
        """Replaces value of `path` kwarg parameter of the object with `path` value from CLI argument.
        
        :param object_kwargs: Colection of object parameters
        :type object_kwargs: list[dict[str, str]]
        :return: Collection of object parameters with `path` replaced with value of `path` CLI argument 
        :rtype: list[dict[str, str]]
        """

        logger_main.debug("Parsing input reports - report path override")
        [dict.update({'path': self.cli_path}) for dict in object_kwargs]
        #TODO map(lambda dict: dict.update({'path': self.cli_path}), object_kwargs)

        return object_kwargs

    def _parse_input_report(self) -> list[dict[str, Any]]:
        """Orchestrating function for parsing parameters for input reports.

        :return: Collection of ready to use object kwargs.
        :rtype: list[dict[str, Any]]
        """

        logger_main.debug("Parsing input reports")
        
        if self.cli_report:
            _temp_report_params = self._input_report_single_mode_override()
        else:
            _temp_report_params = self._input_report_csv_standard_file_mode()
        
        if self.cli_path:
            _temp_report_params = self._input_report_path_override(_temp_report_params)

        self.report_params = self._input_report_path_cast(_temp_report_params)
        
        logger_main.debug("Input reports successfully generated")

        return self.report_params

    def _create_sfdc_reports(self) -> Generator[SfdcReport, None, None]:
        """SFDC Report objects factory

        :return: Generator with SFDC Reeport objects
        :rtype: Generator[SfdcReport, None, None]
        :yield: SFDC Report instance based on parsed report parameters
        :rtype: SfdcReport
        """

        logger_main.debug("Creating SFDC report objects")
        reports = (SfdcReport(**kwargs) for kwargs in self._parse_input_report())

        return reports
    
    def create_reports(self) -> list[SfdcReport]:
        """Orchestrating function to handle report objects factory

        :return: Collection of SfdcReports
        :rtype: list[SfdcReport]
        """

        logger_main.debug("Creating all report objects")
        self.report_list = list(self._create_sfdc_reports())

        return self.report_list
    
    def create_summary_report(self) -> None:
        """Creates summary report which consist of all important details regarding reports. 
        Report is generated once all the reports are saved.
        """

        logger_main.debug("Creating summary report, saved in %s", self.summary_report_path)
        
        header = ['file_name', 'report_id', 'type', 'valid', 'created_date', 'pull_date', 'processing_time', 'attempt_count', 'file_size'] 
        
        with open(self.summary_report_path, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(header)

            for report in self.report_list:
                writer.writerow([report.name, report.id, report.type, report.valid, report.created_date, 
                                report.pull_date, report.processing_time, report.attempt_count, report.size])
        
        return None
    