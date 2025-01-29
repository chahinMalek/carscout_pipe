from dataclasses import dataclass
from typing import Dict, Any

from src.config import ConfigManager
from src.io.file_service import FileService
from src.scrapers.base import BaseScraper
from typing import Type


@dataclass
class StepContext:
    """Holds the context for pipeline step execution"""
    run_id: str
    config_manager: ConfigManager
    file_service: FileService
    params: Dict[str, Any]
    scraper_class: Type['BaseScraper'] | None = None


class PipelineStep:
    """Base class for pipeline steps"""
    def execute(self, context: StepContext) -> Dict[str, Any]:
        raise NotImplementedError
