import csv
from datetime import datetime
import os
from typing import Protocol, runtime_checkable
import browser_cookie3
import webbrowser
import requests
from time import sleep
from io import StringIO
import pandas as pd

from components.containers import Report, SFDC_Report


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
    
    sid: str|None
    domain: str
    timeout: int
    headers: dict[str, str]
    export_params: str

    def sid_interception(self) -> str|None:
        ...

    def connection_check(self) -> bool:
        ...

    def report_request(self, report: Report) -> str|None:
        ...
    
    def save_to_csv(self, report: Report) -> str:
        ...
    
    @staticmethod
    def load_reports_list(report_list, report_directory):
        ...

    @staticmethod    
    def final_report(result_reports, final_report_path):
        ...

class SFDC_Connector():

    def __init__(self,
        domain='',
        *,
        sid=None,
        timeout=900, 
        headers={'Content-Type': 'application/json', 
                'X-PrettyPrint': '1'}, 
        export_params='?export=&enc=UTF-8&isdtp=p1'):
        
        self.domain = domain
        self.sid = self.sid_interception() if not sid else sid
        self.timeout = timeout
        self.headers = headers
        self.export_params = export_params

    def sid_interception(self):

        try:
            cookie_jar = browser_cookie3.edge()
            domain = self.domain.replace('https://', '').replace('/','')
            sid = [cookie.value for cookie in cookie_jar if cookie.name == 'sid' and cookie.domain == domain]
            return sid[0] if sid else None
        except:
            return None

    def connection_check(self):
        
        print(f'SID checking in progress ...')

        while not self.sid:
            print('SID not found! -> Login to SFDC -> SalesForce webpage will open shortly.')
            sleep(2)
            
            edge_path = '"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --profile-directory=Default %s'
            webbrowser.get(edge_path).open(self.domain)
            
            sleep(30)
            while not self.sid:
                self.sid = self.sid_interception()
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
        
        return self.sid

    def report_request(self, report: SFDC_Report):
        
        report.created_date = datetime.now()
        
        report_url = self.domain + report.report_id + self.export_params

        self.headers['Authorization'] = ''.join(filter(None, ['Bearer ', self.sid]))

        response = requests.get(report_url, 
                                headers=self.headers, 
                                cookies={'sid': str(self.sid)},
                                timeout=self.timeout,
                                allow_redirects=False)

        report.attempt_count += 1

        if response.status_code != 200:
            report.valid = False
            return False
        else:
            report.stream = response.content.decode('utf-8')
            report.valid = True
            return report.stream

    def read_stream(self, report: SFDC_Report) -> tuple:
        
        report.content = pd.read_csv(StringIO(report.stream),   
                                    dtype='string',
                                    low_memory=False)

        return report.content.shape
    
    def save_to_csv(self, report: SFDC_Report) -> str:

        file_path = f'{"/".join([str(report.path), report.file_name])}.csv'

        report.content.to_csv(file_path,
                            index=False)
        
        report.downloaded = True
        report.pull_date = datetime.now()
        
        fsize = round((os.stat(file_path).st_size / (1024 * 1024)),1)
        report.file_size = fsize

        report.processing_time = report.pull_date - report.created_date

        print('|', end='', flush=True)

        return file_path

    def erase_report(self, report: SFDC_Report) -> None:
        report.stream = ""
        report.content = pd.DataFrame()

        return None

    def report_processing(self, report: SFDC_Report, result_reports: list) -> None:
    
        while not report.valid:
            try:
                self.report_request(report)
                self.read_stream(report)
                self.save_to_csv(report)
                self.erase_report(report)
            except pd.errors.EmptyDataError as e:
                print(f'Timeout {report.file_name}, {report.attempt_count}')
                report.valid = False
                continue
            except pd.errors.ParserError as e:
                print(f'Unexpected end of stream {report.file_name}, {report.attempt_count}')
                report.valid = False
                continue
            break
            
        result_reports.append(report)

        return None

    @staticmethod
    def load_reports_list(report_list, report_directory):
    
        reports = {}
        
        with open(report_list) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            
            for row in csv_reader:
                reports[row[0]] = row[1]
        
        return [SFDC_Report(report_id=v, file_name=k, path=report_directory) for k, v in reports.items()]

    @staticmethod    
    def final_report(result_reports, final_report_path):
        header = ['file_name', 'report_id', 'type', 'valid', 'created_date', 'pull_date', 'processing_time', 'attempt_count', 'file_size'] 
        
        with open(str(final_report_path), 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

            writer.writerow(header)

            for report in result_reports:
                writer.writerow([report.file_name, report.report_id, report.type, report.valid, report.created_date, 
                                report.pull_date, report.processing_time, report.attempt_count, report.file_size])
        
        return final_report_path

