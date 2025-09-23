import logging
import sys


def get_logger(name: str, log_level: int = logging.INFO):
    """
    Returns a new logger instance with a standardized formatter and handlers.

    Parameters:
        name (str): The name of the logger (usually `__name__`).
        log_level (int): The name of the logging level (default is `logging.INFO`).

    Returns:
        logging.Logger: Configured logger instance.
    """

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Check if handlers already exist to avoid duplicate logs
    if not logger.hasHandlers():
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(name)s - %(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
