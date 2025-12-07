import os
import pandas as pd

from infra.factory.logger import LoggerFactory
from infra.interfaces.file_service import FileService


class LocalFileService(FileService):
    """Service for reading/writing files from local filesystem"""

    def __init__(self, basedir: str, logger_factory: LoggerFactory):
        self._basedir = basedir
        self._logger = logger_factory.create(self.__class__.__name__)

    def read_csv(self, path: str) -> pd.DataFrame:
        # read relative to basedir
        _full_path = os.path.join(self._basedir, path)
        try:
            df = pd.read_csv(_full_path)
            self._logger.info(f"Successfully read CSV from {path} ({len(df)} rows)")
            return df

        except Exception as e:
            self._logger.error(f"Failed to read CSV file from {path}: {str(e)}")
            raise

    def file_exists(self, path: str) -> bool:
        path = os.path.join(self._basedir, path)
        return os.path.isfile(path)
