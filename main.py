#!/usr/bin/env python3.11

import time
import click
import asyncio
import logging

from queue import Queue

from components.connectors import SfdcConnector
from components.containers import ReportsContainer
from components.handlers import WorkerFactory
from components.config_loaders import load_params, load_env_file
from components.loggers import logger_configurer


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('cli_reports_list_path', required=False, type=click.Path(exists=True))
@click.option('--cli_report', '-r', type=click.STRING, help='Run single report -> "type,name,id,path,optional_report_params"')
@click.option('--cli_path', '-p', type=click.Path(exists=True), help='Override save location of the reports')
@click.option('--cli_threads', '-t', type=click.INT, default=0, show_default=True, help='Number of threads to spawn')
@click.option('--cli_stdout_loglevel', '-ls', type=click.STRING, default="WARNING", show_default=True, help='STDOUT logging level -> [DEBUG | INFO | WARN |WARNING | ERROR | CRITICAL]')
@click.option('--cli_file_loglevel', '-lf', type=click.STRING, default="INFO", show_default=True, help='File logging level -> [DEBUG | INFO | WARN| WARNING | ERROR | CRITICAL]')
@click.option('--verbose', '-v', is_flag=True, show_default=True, default=True, help='Turn on/off progress bar')

def main(cli_reports_list_path, cli_report, cli_path, cli_threads, cli_stdout_loglevel, cli_file_loglevel, verbose):
    """
    SFR is a simple, but very efficient due to scalability, Python application which allows you to download various reports.  
    Program supports asynchronous requests and threading for saving/processing content. Logging and CLI parameters handlig is also included.
    
    So far the App supports SFDC reports with SSO authentication.
    """
    t0 = time.time()
    
    logger_main = logging.getLogger(__name__)
    logger_configurer(cli_stdout_loglevel, cli_file_loglevel, verbose)
    logger_main.info('SFR started')

    load_env_file()

    reports_list_path, summary_report_path = load_params(cli_reports_list_path)

    queue = Queue()
    connector = SfdcConnector(queue, verbose=verbose)
    container = ReportsContainer(reports_list_path, summary_report_path, cli_report, cli_path)
    WorkerFactory(queue, cli_threads, cli_report)
    
    asyncio.run(connector.handle_requests(container.report_list))

    queue.join()

    t1 = time.time()

    container.create_summary_report()

    logger_main.info('SFR finished in %s', time.strftime("%H:%M:%S", time.gmtime(t1 - t0)))

if __name__ == '__main__':
    main()
