import os
import logging
import logging.handlers


def logger_configurer(cli_stdout_loglevel, cli_file_loglevel, verbose) -> None:
    """
        Sets the configuration for logger instance. Supports STDOUT logger and ROTATING FILE logger.

            Returns:
                None
    """
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    
    if verbose:
        slevel = levels.get(cli_stdout_loglevel.lower(), logging.ERROR)
    else: 
        slevel = 20

    flevel = levels.get(cli_file_loglevel.lower(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(slevel)

    log_path = os.path.join(os.path.abspath(__file__), '..', '..', './logs/sfr.log')

    handler_f = logging.handlers.RotatingFileHandler(log_path, 'a', 1_000_000, 3)
    handler_s = logging.StreamHandler()
    
    handler_s.setLevel(flevel)
    formatter = logging.Formatter('%(asctime)-20s| %(levelname)-8s| %(processName)-12s| '
                                  '%(message)s', '%Y-%m-%d %H:%M:%S')
    handler_f.setFormatter(formatter)
    handler_s.setFormatter(formatter)
    
    logger.addHandler(handler_f)
    logger.addHandler(handler_s)

    return None
