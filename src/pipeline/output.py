from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path


@dataclass
class PipelineOutput:
    """Standardized output format for pipeline steps"""

    step_name: str
    output_dir: Path
    num_inputs: int
    num_outputs: int
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the output to a dictionary format"""
        return {
            "step_name": self.step_name,
            "output_dir": str(self.output_dir),
            "num_inputs": self.num_inputs,
            "num_outputs": self.num_outputs,
            "metadata": self.metadata or {},
        }
