import logging
import logging.handlers


def logger_configurer() -> None:
    """
        Creates instance of logger for log listener, set the configuration for logger.

            Returns:
                None
    """
    root = logging.getLogger()
    handler_f = logging.handlers.RotatingFileHandler('./logs/sfr.log', 'a',
                                                   1_000_000, 3)
    handler_s = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)-20s| %(levelname)-8s| %(processName)-12s| '
                                  '%(message)s', '%Y-%m-%d %H:%M:%S')
    handler_f.setFormatter(formatter)
    handler_f.setLevel(logging.DEBUG)
    handler_s.setFormatter(formatter)
    handler_s.setLevel(logging.WARNING)

    root.addHandler(handler_f)
    root.addHandler(handler_s)
