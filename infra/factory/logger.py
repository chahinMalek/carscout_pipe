import logging
import sys
from typing import Any


class LoggerFactory:
    """
    Factory for logger creation.

    Defaults to console logging using the configured `format_str`.
    Includes option to use JSON formatting and context injection.
    This behaviour is controlled through the `use_json` parameter.

    Context can be passed to automatically include fields like run_id and brand in every log message.
    If context is provided, the logger is wrapped with a LoggerAdapter.
    """

    def __init__(
        self,
        format_str: str,
        log_level: int = logging.INFO,
        use_json: bool = False,
    ):
        self._log_level = log_level
        self._format_str = format_str
        self._use_json = use_json

    def create(
        self, name: str, context: dict[str, Any] | None = None
    ) -> logging.Logger | logging.LoggerAdapter:
        """
        Create a logger with the specified name.

        Args:
            name: The logger name (e.g., 'airflow.listings.bmw')
            context: Optional dict of extra fields to include in every log message.
                     Example: {"run_id": "abc-123", "brand": "bmw"}

        Returns:
            A Logger or LoggerAdapter if context is provided.
        """
        logger = logging.getLogger(name)
        logger.setLevel(self._log_level)

        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)

            if self._use_json:
                from pythonjsonlogger import jsonlogger

                formatter = jsonlogger.JsonFormatter(
                    "%(asctime)s %(name)s %(levelname)s %(message)s",
                    rename_fields={"asctime": "timestamp", "levelname": "level"},
                )
            else:
                formatter = logging.Formatter(self._format_str)

            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # disable propagation to prevent enforcing airflow's formatting
            logger.propagate = False

        # wrap with LoggerAdapter if context is provided
        if context:
            return logging.LoggerAdapter(logger, context)
        return logger
