from typing import Protocol

import pandas as pd


class FileService(Protocol):
    """Protocol for IO operations - abstracts storage location (local, S3, etc.)"""

    _basedir: str

    def read_csv(self, path: str) -> pd.DataFrame:
        ...
    
    def file_exists(self, path: str) -> bool:
        ...
