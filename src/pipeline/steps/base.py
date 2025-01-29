from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

from src.config import ConfigManager
from src.io.file_service import FileService

@dataclass
class StepContext:
    """Holds the context for pipeline step execution"""
    run_id: str
    config_manager: ConfigManager
    file_service: FileService
    params: Dict[str, Any]

class PipelineStep:
    """Base class for pipeline steps"""
    def execute(self, context: StepContext) -> Dict[str, Any]:
        raise NotImplementedError
