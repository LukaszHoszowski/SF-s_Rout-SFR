import logging
import asyncio
import os
import requests
import aiohttp
import browser_cookie3
import webbrowser

from typing import Protocol, runtime_checkable
from queue import Queue
from datetime import datetime
from tqdm.asyncio import tqdm
from time import sleep

from components.containers import ReportProtocol


logger_main = logging.getLogger(__name__)


@runtime_checkable
class Connector(Protocol):
    """Protocol class for connector object.

    :param queue: Shared queue object.
    :type queue: Queue
    :param timeout: Request's timeout value in seconds.
    :type timeout: int
    :param headers: Headers required to establish the connection.
    :type headers: dict[str, str]
    """

    queue: Queue
    timeout: int
    headers: dict[str, str]

    def check_connection(self) -> bool:
        """Checks connection with given domain.

        :return: Flag, True if connection is established, False otherwise.
        :rtype: bool
        """
        ...

    async def report_gathering(self, reports: list[ReportProtocol], session: aiohttp.ClientSession) -> None:
        """Collects asynchronous responses from the servers.

        :param reports: Collection of ReportProtocol objects.
        :type reports: list[ReportProt]
        :param session: HTTP client session object to handle request in transaction.
        :type session: aiohttp.ClientSession
        """
        ...


class SfdcConnector():
    """Concrete class representing Connector object for SFDC

    :param queue: Shared queue object.
    :type queue: Queue
    :param verbose: CLI parameter used as switch between progress bar and logging to stdout on INFO level. Defaults to False.
    :type timeout: int
    :param timeout: Request's timeout value in seconds. Defaults to 900.
    :type timeout: int
    :param headers: Headers required to establish the connection. Defaults to {'Content-Type': 'application/csv', 'X-PrettyPrint': '1'}.
    :type headers: dict[str, str]
    :param export_params: Default parameters required by SFDC. Defaults to '?export=csv&enc=UTF-8&isdtp=p1'.
    :type export_params: str
    """

    def __init__(self,
                 queue: Queue,
                 *,
                 cli_verbose: bool = False,
                 timeout: int = 900,
                 headers: dict[str, str] = {'Content-Type': 'application/csv',
                                            'X-PrettyPrint': '1'}):
        """Constructor method for SfdcConnector, automatically checks connection after initialization.

        :param queue: Shared, thread-safe queue.
        :type queue: Queue
        :param verbose: Flag, if True switches to verbose mode and changes loglevel for stdout handler to INFO, if Fales shows progress bar. Defaults to False.
        :type verbose: bool
        :param timeout: Response timeout in seconds. Defaults to 900.
        :type timeout: int
        :param headers: Headers for the request. Defaults to {'Content-Type': 'application/csv', 'X-PrettyPrint': '1'}.
        :type headers: dict[str, str]
        """

        self.queue = queue
        self.cli_verbose = cli_verbose
        self.domain = str(os.getenv("SFDC_DOMAIN"))
        self.timeout = timeout
        self.headers = headers
        self.sid = self._intercept_sid()
        self.edge_path = '"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --profile-directory=Default %s'

        self.check_connection()

    def _convert_domain_for_cookies_lookup(self) -> str:
        """Converts domain as key in cookier for sid lookup.

        :return: Converted url complaiant with cookies keys.
        :rtype: str
        """

        logger_main.debug("Parsing domain key for cookies")
        return self.domain.replace('https://', '').replace('/', '')

    def _intercept_sid(self) -> str:
        """Intercepts sid from MS Edge's CookieJar.

        :return: Intercepted `sid` or empty string if `sid` doesn't exist.
        :rtype: str
        """

        logger_main.info('SID interception started')
        try:
            logger_main.debug("Trying to access MS Edge's CookieJar")
            cookie_jar = browser_cookie3.edge()

            logger_main.debug("Retrieving SID entry from CookieJar")
            sid = [cookie.value for cookie in cookie_jar if cookie.name ==
                   'sid' and cookie.domain == self._convert_domain_for_cookies_lookup()]

            return sid[0] or ""
        except:
            logger_main.debug("SID entry not there")

            return ""

    def _open_sfdc_site(self) -> None:
        """Opens SFDC website on given domain url if `sid`

        """
        logger_main.warning(
            'SID not found! -> Login to SFDC -> SalesForce webpage will open shortly')
        sleep(2)

        logger_main.debug('Openning SFDC webside to log in to SalesForce')
        webbrowser.get(self.edge_path).open(self.domain)

        logger_main.debug(
            "Starting 30 sec sleep to let user log in to SalesForce")
        sleep(30)
        while not self.sid:
            self.sid = self._intercept_sid()
            logger_main.info('intercepting SID! Hold on tight!')
            sleep(2)

        return None

    def _parse_headers(self) -> None:
        """Parses headers for request.
        """

        logger_main.debug("Parsing headers for SFDC request check")
        self.headers['Authorization'] = ''.join(
            filter(None, ['Bearer ', self.sid]))

        return None

    def check_connection(self) -> bool:
        """Checks the connection with given domain.

        :return: Flag, True if connection was successful, False wasn't.
        :rtype: bool
        """

        logger_main.info("SID checking in progress ...")

        while not self.sid:
            self._open_sfdc_site()

        logger_main.info('SID found!')

        self._parse_headers()

        logger_main.debug("Checking SID validity")
        response = requests.get(self.domain,
                                cookies={'sid': self.sid},
                                allow_redirects=True)
        if response.headers['Cache-Control'] == 'private':
            logger_main.info('SID ok!')
        else:
            logger_main.critical('SID not ok!!!')
            self.sid = None
            return False

        return True

    def _parse_report_url(self, report: ReportProtocol) -> str:
        """Parses report object url.

        :param report: Instance of `ReportProtocol`.
        :type report: ReportProtocol
        :return: Parsed url.
        :rtype: str
        """
        return self.domain + report.id + report.export_params

    async def _request_report(self, report: ReportProtocol, session: aiohttp.ClientSession) -> None:
        """Sends asynchronous request to given domain with given parameters within shared session. Checks response status:
        - 200: response is saved in `ReportProtocol.response`, `ReportProtocol.valid` set to True, ReportProtocol is being put to the `queue`.
        - 404: error in response, `ReportProtocol.valid` set to False, no retries.
        - 500: request timeour, `ReportProtocol.valid` set to False, another attempt.
        - *: unknown error, `ReportProtocol.valid` set to False, another attempt.

        :param report: Instance of `ReportProtocol`.
        :type report: ReportProtocol
        :param session: Shared session object.
        :type session: aiohttp.ClientSession
        """

        report.created_date = datetime.now()

        report_url = self._parse_report_url(report)

        logger_main.info("%s -> Sending request", report.name)
        logger_main.debug(
            "Sending asynchronous report request with params: %s, %s", report_url, self.headers)

        while not report.valid and report.attempt_count < 20:
            async with session.get(report_url,
                                   headers=self.headers,
                                   cookies={'sid': str(self.sid)},
                                   timeout=self.timeout,
                                   allow_redirects=True) as r:

                report.attempt_count += 1

                if r.status == 200:
                    logger_main.info(
                        "%s -> Request successful, retrieving content", report.name)
                    try:
                        report.response = await r.text()
                        report.valid = True
                        logger_main.debug(
                            "Sending the content to the queue for processing, %s elements in the queue before transfer", self.queue.qsize())
                        self.queue.put(report)
                        logger_main.debug(
                            '%s succesfuly downloaded and put to the queue', report.name)
                    except aiohttp.ClientPayloadError as e:
                        logger_main.warning(
                            '%s is invalid, Unexpected end of stream, SFDC just broke the connection -> %s', report.name, e)
                        continue
                elif r.status == 404:
                    logger_main.error(
                        "%s is invalid, Report does not exist - check ID, SFDC respond with status %s - %s", report.name, r.status, r.reason)
                    report.valid = False
                    break
                elif r.status == 500:
                    logger_main.warning(
                        "%s is invalid, Timeout, SFDC respond with status %s - %s", report.name, r.status, r.reason)
                    report.valid = False
                else:
                    logger_main.warning(
                        "%s is invalid, Unknown Error, SFDC respond with status %s - %s", report.name, r.status, r.reason)
                    report.valid = False
        return None

    async def _toggle_progress_bar(self, tasks: list[asyncio.Task]) -> None:
        """Toggles between showing progress bar and logging on INFO level.

        :param tasks: Collection of asynchronous request tasks.
        :type tasks: list[asyncio.Task]
        """

        if self.cli_verbose:
            _ = [await task_ for task_ in tqdm.as_completed(tasks, total=len(tasks))]

    def _create_async_tasks(self, reports: list[ReportProtocol], session: aiohttp.ClientSession) -> list[asyncio.Task]:
        """Creates collection of asynchronous request tasks. 

        :param reports: Collection of `ReportsProtocol' instances.
        :type reports: list[ReportProtocol]
        :param session: Shared, asynchronous session.
        :type session: aiohttp.ClientSession
        :return: Collection of asynchronous request tasks.
        :rtype: list[asyncio.Task]
        """

        logger_main.debug("Creating tasks for asynchronous processing")
        return [asyncio.create_task(self._request_report(report, session)) for report in reports]

    async def _report_request_all(self, reports: list[ReportProtocol], session: aiohttp.ClientSession) -> None:
        """Orchestrates entire process of processing tasks.

        :param reports: Collection of `ReportProtocol` instances.
        :type reports: list[ReportProtocol]
        :param session: Shared asyncio session.
        :type session: aiohttp.ClientSession
        """

        tasks = self._create_async_tasks(reports, session)

        await self._toggle_progress_bar(tasks)

        await asyncio.gather(*tasks)

        return None

    async def handle_requests(self, reports: list[ReportProtocol]) -> None:
        """Creates session and process asynchronous tasks.

        :param reports: Collection of `ReportProtocol` instances.
        :type reports: list[ReportProtocol]
        """

        logger_main.debug("Awaiting responses")
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await self._report_request_all(reports, session)

        return None

if __name__ == '__main__':
    pass
