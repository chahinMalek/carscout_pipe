import logging
import sys


def get_logger(name: str, log_level: str = "info"):
    """
    Returns a new logger instance with a standardized formatter and handlers.

    Parameters:
        name (str): The name of the logger (usually `__name__`).
        log_level (str): The name of the logging level (default is `info`).

    Returns:
        logging.Logger: Configured logger instance.
    """

    logger = logging.getLogger(name)
    log_level = logging._nameToLevel.get(log_level.upper(), logging.INFO)
    logger.setLevel(log_level)  # Set the logger level

    # Check if handlers already exist to avoid duplicate logs
    if not logger.hasHandlers():
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
