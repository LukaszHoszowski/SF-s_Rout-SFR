"""
requests.adapters
~~~~~~~~~~~~~~~~~
This module contains the transport adapters that Requests uses to define
and maintain connections.
"""

import os
import logging
import logging.handlers


def logger_configurer(*,
                      cli_stdout_loglevel: str, 
                      cli_file_loglevel: str, 
                      cli_verbose: bool) -> None:
    """
    Configures logger settings for file and stdout handlers.

    :param cli_stdout_loglevel: LogLevel for stdout logger handler based on CLI option. Defaults to ERROR.
    :type cli_stdout_loglevel: str
    :param cli_file_loglevel: LogLevel for file logger handler based on CLI option. Defaults to INFO.
    :type cli_stdout_loglevel: str
    :param verbose: Flag toggling LogLevel for stdout logger handler, if True sets to ERROR, else INFO.
    :type verbose: str
    """

    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }

    if cli_verbose:
        slevel = levels.get(cli_stdout_loglevel.lower(), logging.ERROR)
    else:
        slevel = 20

    flevel = levels.get(cli_file_loglevel.lower(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(slevel)

    log_path = os.path.join(os.path.abspath(__file__),
                            '..', '..', './logs/sfr.log')

    handler_f = logging.handlers.RotatingFileHandler(
        log_path, 'a', 1_000_000, 3)
    handler_s = logging.StreamHandler()

    handler_s.setLevel(flevel)
    formatter = logging.Formatter('%(asctime)-20s| %(levelname)-8s| %(processName)-12s| '
                                  '%(message)s', '%Y-%m-%d %H:%M:%S')
    handler_f.setFormatter(formatter)
    handler_s.setFormatter(formatter)

    logger.addHandler(handler_f)
    logger.addHandler(handler_s)

    return None

if __name__ == '__main__':
    pass
