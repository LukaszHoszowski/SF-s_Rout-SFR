import asyncio
import logging
from queue import Queue
import aiohttp
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable
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
    
    domain: str
    queue: Queue
    timeout: int
    headers: dict[str, str]|None
    export_params: str|None
    reports: list[Optional[Report]] 

    def connection_check(self) -> bool:
        ...

    def report_request(self, report: Report) -> str|None:
        ...
        
    def load_reports_list(self, report_directory):
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
            logger_main.error("Coudn't retrieve SID entry")
            return None

    def connection_check(self) -> None:
        
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
        
        return None

    async def _report_request(self, report: SfdcReport, session) -> None:

        report.created_date = datetime.now()
        
        report_url = self.domain + report.id + self.export_params

        logger_main.debug("Sending asynchronous report request with params: %s, %s", report_url, self.headers)
        
        while not report.valid:
            async with session.get(report_url, 
                                    headers=self.headers, 
                                    cookies={'sid': str(self.sid)},
                                    timeout=self.timeout,
                                    allow_redirects=True) as r:

                report.attempt_count += 1

                if r.status != 200:
                    logger_main.warning("%s invalid, check ID, is SFDC alive", report.name)
                    report.valid = False
                else:
                    logger_main.debug("%s -> Request successful, retrievieng content", report.name)
                    report.response = await r.text()
                    report.valid = True
                    logger_main.debug("Sending the content to the queue for processing, %s elements in the queue before transfer", self.queue.qsize())
                    self.queue.put(report)
                    logger_main.debug('%s succesfuly downloaded and put to the queue', report.name)
        
        return None
    
    async def _report_request_all(self, reports: list[SfdcReport], session) -> None:

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
        timeout = aiohttp.ClientTimeout(total=1_800)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await self._report_request_all(reports, session)

        return None