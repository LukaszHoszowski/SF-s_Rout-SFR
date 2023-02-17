import asyncio
import csv
import aiohttp
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable
import browser_cookie3
import webbrowser
from time import sleep

import requests

from components.containers import Report, SfdcReport


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
        domain='',
        *,
        sid=None,
        timeout=900, 
        headers={'Content-Type': 'application/csv', 
                'X-PrettyPrint': '1'}, 
        export_params='?export=csv&enc=UTF-8&isdtp=p1',
        reports=[]):
        
        self.domain = domain
        self.sid = self._sid_interception() if not sid else sid
        self.timeout = timeout
        self.headers = headers
        self.export_params = export_params
        self.reports = reports

    def _sid_interception(self):

        try:
            cookie_jar = browser_cookie3.edge()
            domain = self.domain.replace('https://', '').replace('/','')
            sid = [cookie.value for cookie in cookie_jar if cookie.name == 'sid' and cookie.domain == domain]
            return sid[0] if sid else None
        except:
            return None

    def connection_check(self) -> None:
        
        print(f'SID checking in progress ...')

        while not self.sid:
            print('SID not found! -> Login to SFDC -> SalesForce webpage will open shortly.')
            sleep(2)
            
            edge_path = '"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --profile-directory=Default %s'
            webbrowser.get(edge_path).open(self.domain)
            
            sleep(30)
            while not self.sid:
                self.sid = self._sid_interception()
                print('intercepting SID! Hold on tight!')
                sleep(2)
            
        print(f'SID found!')

        self.headers['Authorization'] = 'Bearer ' + self.sid
        response = requests.get(self.domain, 
                                cookies={'sid': self.sid},
                                allow_redirects=True)
        if response.headers['Cache-Control'] == 'private':
            print('SID ok!')
        else:
            self.sid = None
        
        return None

    def load_reports(self, report_list: str, report_directory: str) -> None:
    
        reports = {}
        
        with open(report_list) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            
            for row in csv_reader:
                reports[row[0]] = row[1]
        
        self.reports = [SfdcReport(report_id=v, file_name=k, path=report_directory) for k, v in reports.items()]

        return None

    async def _report_request(self, report: SfdcReport, session) -> None:
        
        print(f'Starting {report.file_name}')

        report.created_date = datetime.now()
        
        report_url = self.domain + report.report_id + self.export_params

        self.headers['Authorization'] = ''.join(filter(None, ['Bearer ', self.sid]))

        async with session.get(report_url, 
                                headers=self.headers, 
                                cookies={'sid': str(self.sid)},
                                timeout=self.timeout,
                                allow_redirects=True) as r:

            report.attempt_count += 1

            if r.status != 200:
                report.valid = False
            else:
                report.content = await r.text()
                print(f'Downloaded {report.file_name}')

        return None
    
    async def _report_request_all(self, reports: list[SfdcReport], session) -> None:
        tasks = []
        for report in reports:
            task = asyncio.create_task(self._report_request(report, session))
            tasks.append(task)
        res = await asyncio.gather(*tasks)
        return res
    
    async def report_gathering(self, reports: list[SfdcReport]) -> None:
        async with aiohttp.ClientSession() as session:
            responses = await self._report_request_all(reports, session)
