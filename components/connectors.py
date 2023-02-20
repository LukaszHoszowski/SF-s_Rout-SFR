import asyncio
import logging
from queue import Queue
import aiohttp
from datetime import datetime
from typing import Protocol, runtime_checkable
import browser_cookie3
import webbrowser
from time import sleep

import requests
from tqdm.asyncio import tqdm

from components.containers import Report, SfdcReport


logger_main = logging.getLogger(__name__)

@runtime_checkable
class Connector(Protocol):
    """
    A Protocol class as a scaffold for connector objects.
    
    ...
    
    Attributes
    ----------
    domain: str
        sfdc domain -> "https://<your_org>.com/"
    queue: Quoue
        instance of Queue for report sharing
    timeout: int
        request timeout in seconds
    headers: dict[str, str]
        required request headers
    export_params: str
        additional export parameters
    report: str
        report container

    Methods
    ----------    
    def connection_check(self) -> bool:
        returns True is connection was succesful, False if wasn't able to establish the connection
    
    def report_gathering(self, reports: list[Report], session: aiohttp.ClientSession) -> None:
        sends requests asynchronously to given domain and save them inside report objects
    """
    
    domain: str
    queue: Queue
    timeout: int
    headers: dict[str, str]
    export_params: str

    def connection_check(self) -> bool:
        ...

    def report_gathering(self, reports: list[Report], session: aiohttp.ClientSession) -> None:
        ...
    
class SfdcConnector():

    def __init__(self,
        
        domain,
        queue,
        *,
        sid=None,
        timeout=900, 
        headers={'Content-Type': 'application/csv', 
                'X-PrettyPrint': '1'}, 
        export_params='?export=csv&enc=UTF-8&isdtp=p1'):

        self.domain = domain
        self.queue = queue
        self.sid = self._sid_interception() if not sid else sid
        self.timeout = timeout
        self.headers = headers
        self.export_params = export_params

    def _sid_interception(self) -> str|None:
        
        logger_main.info('SID interception started')
        try:
            logger_main.debug("Trying to access MS Edge's CookieJar")
            cookie_jar = browser_cookie3.edge()
            logger_main.debug("Parsing domain key for cookies")
            domain = self.domain.replace('https://', '').replace('/','')
            logger_main.debug("Retrieving SID entry from CookieJar")
            sid = [cookie.value for cookie in cookie_jar if cookie.name == 'sid' and cookie.domain == domain]
            return sid[0] or None
        except:
            logger_main.debug("SID entry not there")
            return None

    def connection_check(self) -> bool:
        
        logger_main.info("SID checking in progress ...")

        while not self.sid:
            logger_main.warning('SID not found! -> Login to SFDC -> SalesForce webpage will open shortly')
            sleep(2)
            
            edge_path = '"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --profile-directory=Default %s'
            logger_main.debug('Openning SFDC webside to log in to SalesForce')
            webbrowser.get(edge_path).open(self.domain)
            
            logger_main.debug("Starting 30 sec sleep to let user log in to SalesForce")
            sleep(30)
            while not self.sid:
                self.sid = self._sid_interception()
                logger_main.info('intercepting SID! Hold on tight!')
                sleep(2)
            
        logger_main.info('SID found!')

        logger_main.debug("Parsing headers for SFDC request check")
        self.headers['Authorization'] = ''.join(filter(None, ['Bearer ', self.sid]))
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

    async def _report_request(self, report: SfdcReport, session: aiohttp.ClientSession) -> None:

        report.created_date = datetime.now()
        
        report_url = self.domain + report.id + (report.params if report.params else self.export_params)

        logger_main.debug("Sending asynchronous report request with params: %s, %s", report_url, self.headers)
        
        while not report.valid and report.attempt_count < 20:
            async with session.get(report_url, 
                                    headers=self.headers, 
                                    cookies={'sid': str(self.sid)},
                                    timeout=self.timeout,
                                    allow_redirects=True) as r:

                report.attempt_count += 1

                if r.status == 200:
                    logger_main.debug("%s -> Request successful, retrievieng content", report.name)
                    try:
                        report.response = await r.text()
                        report.valid = True
                        logger_main.debug("Sending the content to the queue for processing, %s elements in the queue before transfer", self.queue.qsize())
                        self.queue.put(report)
                        logger_main.debug('%s succesfuly downloaded and put to the queue', report.name)
                    except aiohttp.ClientPayloadError as e:
                        logger_main.warning('%s is invalid, Unexpected end of stream, SFDC just borke the connection', report.name)
                        continue
                elif r.status == 404:
                    logger_main.error("%s is invalid, Report does not exist - check ID, SFDC respond with status %s - %s", report.name, r.status, r.reason)
                    report.valid = False
                    break
                elif r.status == 500:
                    logger_main.error("%s is invalid, Report not reachable - no access to the report, SFDC respond with status %s - %s", report.name, r.status, r.reason)
                    report.valid = False
                    break
                else:
                    logger_main.warning("%s is invalid, Timeout, SFDC respond with status %s - %s", report.name, r.status, r.reason)
                    report.valid = False
        return None
    
    async def _report_request_all(self, reports: list[SfdcReport], session: aiohttp.ClientSession) -> None:

        tasks = []

        logger_main.debug("Creating tasks for asynchronous processing")
        for report in reports:
            task = asyncio.create_task(self._report_request(report, session))
            tasks.append(task)

        _ = [await task_ for task_ in tqdm.as_completed(tasks, total=len(tasks))]

        await asyncio.gather(*tasks)
        
        return None
    
    async def report_gathering(self, reports: list[SfdcReport]) -> None:

        logger_main.debug("Awaiting content")
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await self._report_request_all(reports, session)

        return None