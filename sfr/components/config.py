import os
import csv
import logging

from pathlib import Path
from typing import Any, Protocol
from dotenv import load_dotenv

from components.exceptions import EnvFileNotPresent


logger_main = logging.getLogger(__name__)


class ConfigProtocol(Protocol):
    """Protocol class for config object.

    :param cli_reports_list_path: CLI argument for input report list path.
    :type cli_reports_list_path: str
    :param cli_report: CLI argument for single report params.
    :type cli_report: str
    :param cli_path: CLI argument for save location path override.
    :type cli_path: str
    :param cli_threads: CLI argument for number of threads to use.
    :type cli_threads: int
    """

    cli_reports_list_path: str
    cli_report: str
    cli_path: str
    cli_threads: int

    @staticmethod
    def load_env_file() -> None:
        """Loads system environment variables.
        """
        ...


class Config:
    """Concrete class representing Config object. Contains entire configuration required for a program.
    """

    def __init__(self,
                 cli_reports_list_path: str,
                 cli_report: str,
                 cli_path: str,
                 cli_threads: int):
        """Concrete class representing ReportContainer object. 

        :param cli_reports_list_path: CLI argument for input report list path.
        :type cli_reports_list_path: str
        :param cli_report: CLI argument for single report params.
        :type cli_report: str
        :param cli_path: CLI argument for save location path override.
        :type cli_path: str
        :param cli_threads: CLI argument for number of threads to use.
        :type cli_threads: int
        """

        self.load_env_file()

        self.cli_reports_list_path: str = cli_reports_list_path
        self.cli_report: list[str] = cli_report.split(
            ',') if cli_report else []
        self.cli_path: str = cli_path
        self.summary_report_path: os.PathLike = Path(
            os.path.abspath(str(os.getenv("SUMMARY_REPORTS_PATH"))))
        self.cli_threads: int = cli_threads
        self.keys: list[str] = ['type', 'name', 'id', 'path', 'params']

        self.reports_list_path: os.PathLike = self._define_reports_list_path()
        self.report_params_list: list[dict[str,
                                           str | Path]] = self._parse_input_report()
        self.threads: int = self._define_number_of_threads()

    @staticmethod
    def load_env_file() -> None:
        """Loads .env config file from root folder.
        """
        try:
            logger_main.debug('Loading .env parameters')
            load_dotenv()
        except EnvFileNotPresent:
            logger_main.critical('.env file missing')

        return None

    def _define_number_of_threads(self):
        """Defines number of threads. By default number of threads is set to half of available threads.
        If threads value is not available number of threds will be set to 2. 
        If threads number has been defined in CLI configuration threads will be equal to this number. 
        If CLI report is filled (single report mode) then number of threads will be automatically set to 1  
        """

        return (int((os.cpu_count() or 4) / 2) if not self.cli_threads else self.cli_threads) if not self.cli_report else 1

    def _define_reports_list_path(self) -> os.PathLike:
        if self.cli_reports_list_path:
            return Path(self.cli_reports_list_path)
        else:
            return Path(os.path.abspath(str(os.getenv("DEF_REPORTS_LIST_PATH"))))

    def _input_report_path_cast(self, object_kwargs: list[dict[str, Any]]) -> list[dict[str, str | os.PathLike]]:
        """Casts value of `path` key into Path object. 

        :param object_kwargs: Colection of object parameters
        :type object_kwargs: list[dict[str, Any]]
        :return: Collection of object parameters with `path` casted to Path object 
        :rtype: list[dict[str, str | PathLike]]
        """

        logger_main.debug(
            "Parsing input reports - casting 'path' to Path object")

        [dict.update({'path': Path(dict['path'])}) for dict in object_kwargs]

        return object_kwargs

    def _input_report_single_mode_override(self) -> list[dict[str, str]]:
        """Reads parameters taken from CLI. Returns parsed parameters into object kwargs. 

        :return: collection of single object kwargs (parameters) based on CLI argument
        :rtype: list[dict[str, str]]
        """

        logger_main.debug("Parsing input reports - single mode report")

        if len(self.cli_report) != 5:
            logger_main.debug(
                "Parsing input reports - single mode report | optional_params not present")
            self.cli_report.append('')

        return [dict(zip(self.keys, self.cli_report))]

    def _input_report_csv_standard_file_mode(self) -> list[dict[str, str]]:
        """Reads parameteres taken from input CSV. Returns parsed parameters into objects kwargs.

        :return: collection of objects kwargs (parameters) based on input CSV
        :rtype: list[dict[str, str]]
        """

        logger_main.debug("Parsing input reports - standard csv mode report")
        with open(self.reports_list_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            logger_main.debug(
                "Parsing input reports - standard csv mode report - skipping header")
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
        # TODO map(lambda dict: dict.update({'path': self.cli_path}), object_kwargs)

        return object_kwargs

    def _parse_input_report(self) -> list[dict[str, Any]]:
        """Orchestrating function for parsing parameters for input reports.

        :return: Collection of ready to use object kwargs.
        :rtype: list[dict[str, Any]]
        """

        logger_main.debug("Parsing input reports")

        _temp_report_params = ""

        if self.cli_report:
            _temp_report_params = self._input_report_single_mode_override()
        else:
            _temp_report_params = self._input_report_csv_standard_file_mode()

        if self.cli_path:
            _temp_report_params = self._input_report_path_override(
                _temp_report_params)

        logger_main.debug("Input reports successfully generated")

        return self._input_report_path_cast(_temp_report_params)
    
if __name__ == '__main__':
    pass
