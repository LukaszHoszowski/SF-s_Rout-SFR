#!/usr/bin/env python3

import asyncio
import logging
import os
from queue import Queue
import time

from components.connectors import SfdcConnector
from components.containers import ReportContainer
from components.file_handler import FileSaveHandler
from components.internals import load_params, load_env_file
from components.logs import logger_configurer


if __name__ == '__main__':

    t0 = time.time()
    
    logger_main = logging.getLogger(__name__)
    logger_configurer()
    logger_main.info('SFR started')

    load_env_file()

    report_list_path, summary_report_path = load_params()

    queue = Queue()

    domain = str(os.getenv("SFDC_DOMAIN"))

    connector = SfdcConnector(domain, queue)
    container = ReportContainer(report_list_path, summary_report_path)

    connector.connection_check()
    container.create_reports()
    
    num_of_workers = int((os.cpu_count() or 4) / 2)

    for num in range(num_of_workers):
        worker = FileSaveHandler(queue)
        worker.name = f'Slave-{num}'
        worker.daemon = True
        worker.start()
    
    asyncio.run(connector.report_gathering(container.report_list))

    queue.join()

    t1 = time.time()

    container.create_summary_report()

    logger_main.info('SFR finished in %s', (t1 - t0))
