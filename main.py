#!/usr/bin/env python3.11

import os
import time
import click
import asyncio
import logging

from queue import Queue

from components.connectors import SfdcConnector
from components.containers import ReportsContainer
from components.file_handler import WorkerFactory
from components.internals import load_params, load_env_file
from components.logs import logger_configurer


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('reports_list_path', required=False, type=click.Path(exists=True))
@click.option('--cli_report', '-r', help='Run single report -> "type,name,id,path,optional_report_params"')
@click.option('--cli_path', '-p', type=click.Path(exists=True), help='Override save location of the reports')
@click.option('--cli_threads', '-t', default=0, show_default=True, help='Number of threads to spawn')
@click.option('--cli_stdout_loglevel', '-ls', default="WARNING", show_default=True, help='STDOUT logging level -> [DEBUG | INFO | WARN |WARNING | ERROR | CRITICAL]')
@click.option('--cli_file_loglevel', '-lf', default="INFO", show_default=True, help='File logging level -> [DEBUG | INFO | WARN| WARNING | ERROR | CRITICAL]')
@click.option('--verbose', '-v', is_flag=True, show_default=True, default=True, help='Turn on/off progress bar')

def main(reports_list_path, cli_report, cli_path, cli_threads, cli_stdout_loglevel, cli_file_loglevel, verbose):
    """
    SFR is a simple, but very efficient due to scalability, Python application which allows you to download various reports.  
    Program supports asynchronous requests and threading for saving/processing files. Logging and CLI parameters handlig is also included.
    
    So far the App supports SFDC reports with SSO authentication.
    """
    t0 = time.time()
    
    logger_main = logging.getLogger(__name__)
    logger_configurer(cli_stdout_loglevel, cli_file_loglevel, verbose)
    logger_main.info('SFR started')

    load_env_file()

    report_list_path, summary_report_path = load_params(reports_list_path)

    queue = Queue()

    domain = str(os.getenv("SFDC_DOMAIN"))

    connector = SfdcConnector(domain, verbose, queue)
    
    container = ReportsContainer(report_list_path, summary_report_path, cli_report, cli_path)
    
    WorkerFactory(queue, cli_threads, cli_report)
    
    asyncio.run(connector.report_gathering(container.report_list))

    queue.join()

    t1 = time.time()

    container.create_summary_report()

    logger_main.info('SFR finished in %s', time.strftime("%H:%M:%S", time.gmtime(t1 - t0)))

if __name__ == '__main__':
    main()
