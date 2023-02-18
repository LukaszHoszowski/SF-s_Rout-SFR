import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from components.report_exceptions import EnvFileNotPresent


logger_main = logging.getLogger(__name__)

def load_params() -> tuple[Path, Path, Path]:

    logger_main.info('Loading parameters')

    try:
        logger_main.debug('Checking CLI parameters')
        cli_path_input = sys.argv[1]
        cli_path_output = sys.argv[2]
        logger_main.info('%s CLI parameters found', len(sys.argv[1:]))
    except:
        logger_main.debug("CLI parameters hasn't been detected, proceeding with default paths")
        cli_path_input = ''
        cli_path_output = ''
        
    if cli_path_input:
        logger_main.debug('Assigning Input CLI parameter')
        report_list = cli_path_input
    else:
        logger_main.debug('Parsing absolute path for Input parameter')
        report_list = os.path.abspath(str(os.getenv("REPORT_LIST_PATH")))

    if cli_path_output:
        logger_main.debug('Assigning Output CLI parameter')
        report_directory = cli_path_output
    else:
        logger_main.debug('Parsing absolute path for Output parameter')
        report_directory = os.path.abspath(str(os.getenv("REPORT_DIRECTORY")))
        
    logger_main.debug('Parsing absolute path for Summary_report_path parameter')
    summary_report_path = os.path.abspath(str(os.getenv("SUMMARY_REPORT_PATH")))
    
    logger_main.debug('Transforming paths into Path objects')
    paths = tuple(map(lambda path: Path(path), (report_list, report_directory, summary_report_path)))

    return paths

def load_env_file() -> None:
    try:
        logger_main.debug('Loading .env parameters')
        load_dotenv()
    except EnvFileNotPresent:
        logger_main.critical('.env file missing')
    
    return None
