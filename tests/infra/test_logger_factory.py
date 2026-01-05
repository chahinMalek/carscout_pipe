import logging

import pytest

from infra.factory.logger import LoggerFactory


@pytest.mark.unit
class TestLoggerFactory:
    def test_create(self):
        factory = LoggerFactory(
            format_str="%(name)s - %(levelname)s - %(message)s",
            log_level=logging.INFO,
        )
        logger = factory.create("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

    def test_logger_can_log_messages(self):
        factory = LoggerFactory(
            format_str="%(name)s - %(message)s",
            log_level=logging.DEBUG,
        )
        logger = factory.create("test_logger_logging")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

    def test_create_multiple(self):
        factory = LoggerFactory(
            format_str="%(message)s",
            log_level=logging.INFO,
        )
        logger1 = factory.create("logger1")
        logger2 = factory.create("logger2")

        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger1 is not logger2

    def test_logger_does_not_duplicate_handlers(self):
        factory = LoggerFactory(
            format_str="%(message)s",
            log_level=logging.INFO,
        )
        logger1 = factory.create("test_logger")
        logger2 = factory.create("test_logger")

        assert len(logger1.handlers) == len(logger2.handlers)
