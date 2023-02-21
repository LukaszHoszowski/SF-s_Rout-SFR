import os
import logging

from pathlib import Path
from dotenv import load_dotenv

from components.report_exceptions import EnvFileNotPresent


logger_main = logging.getLogger(__name__)

def load_params(reports_list_path) -> tuple[Path, Path]:

    logger_main.info('Loading parameters')
    
    if reports_list_path:
        logger_main.debug('Assigning Input CLI parameter')
        report_list = reports_list_path
    else:
        logger_main.debug('Parsing absolute path for Input parameter based on .env')
        report_list = os.path.abspath(str(os.getenv("REPORT_LIST_PATH")))
        
    logger_main.debug('Parsing absolute path for summary_report_path parameter')
    summary_report_path = os.path.abspath(str(os.getenv("SUMMARY_REPORT_PATH")))
     
    logger_main.debug('Transforming paths into Path objects')
    paths = tuple(map(lambda path: Path(path), (report_list, summary_report_path)))

    return paths

def load_env_file() -> None:
    try:
        logger_main.debug('Loading .env parameters')
        load_dotenv()
    except EnvFileNotPresent:
        logger_main.critical('.env file missing')
    
    return None
