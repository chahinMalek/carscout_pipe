import logging
import sys


class LoggerFactory:
    def __init__(
        self,
        format: str,
        log_level: int = logging.INFO,
    ):
        self._log_level = log_level
        self._format = format

    def create(self, name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(self._log_level)
        if not logger.hasHandlers():
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(self._format)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        return logger
