from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Union, List

import pandas as pd
import shutil


class FileService(ABC):
    """Abstract base class defining interface for file operations"""

    @abstractmethod
    def make_directory(self, path: Union[str, Path], parents: bool = False) -> None:
        """Create a directory at the specified path"""
        pass

    @abstractmethod
    def remove_directory(self, path: Union[str, Path]) -> None:
        """Remove directory at the specified path"""
        pass

    @abstractmethod
    def directory_exists(self, path: Union[str, Path]) -> bool:
        """Check if directory exists at the specified path"""
        pass

    @abstractmethod
    def list_files(self, path: Union[str, Path], pattern: str = "*") -> List[Path]:
        """List all files in the specified directory"""
        pass

    @abstractmethod
    def file_exists(self, path: Union[str, Path]) -> bool:
        """Check if file exists at the specified path"""
        pass

    @abstractmethod
    def read_csv(self, path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Read CSV file into pandas DataFrame"""
        pass

    @abstractmethod
    def write_csv(self, df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
        """Write pandas DataFrame to CSV file"""
        pass

    @abstractmethod
    def read_parquet(self, path: Union[str, Path], **kwargs) -> pd.DataFrame:
        """Read Parquet file into pandas DataFrame"""
        pass

    @abstractmethod
    def write_parquet(self, df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
        """Write pandas DataFrame to Parquet file"""
        pass

    @abstractmethod
    def write_parquet_chunked(
        self, df: pd.DataFrame, path: Union[str, Path], chunk_size: int, **kwargs
    ) -> None:
        """Write pandas DataFrame to Parquet file in chunks"""
        pass

    @abstractmethod
    def read_file(self, path: Union[str, Path], **kwargs) -> Any:
        """Read file based on extension"""
        pass

    @abstractmethod
    def read_lines(self, path: Union[str, Path]) -> List[str]:
        """Read lines from a text file"""
        pass


class LocalFileService(FileService):
    """Implementation of FileService for local filesystem"""

    def make_directory(self, path: Union[str, Path], parents: bool = False) -> None:
        path = Path(path)
        path.mkdir(parents=parents, exist_ok=True)

    def remove_directory(self, path: Union[str, Path]) -> None:
        if self.directory_exists(path):
            shutil.rmtree(path, ignore_errors=True)

    def directory_exists(self, path: Union[str, Path]) -> bool:
        path = Path(path)
        return path.is_dir()

    def list_files(self, path: Union[str, Path], pattern: str = "*") -> List[Path]:
        path = Path(path)
        return list(path.glob(pattern))

    def file_exists(self, path: Union[str, Path]) -> bool:
        path = Path(path)
        return path.is_file()

    def read_csv(self, path: Union[str, Path], **kwargs) -> pd.DataFrame:
        return pd.read_csv(path, **kwargs)

    def write_csv(self, df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
        df.to_csv(path, **kwargs)

    def read_parquet(self, path: Union[str, Path], **kwargs) -> pd.DataFrame:
        return pd.read_parquet(path, **kwargs)

    def write_parquet(self, df: pd.DataFrame, path: Union[str, Path], **kwargs) -> None:
        df.to_parquet(path, **kwargs)

    def write_parquet_chunked(
        self, df: pd.DataFrame, path: Union[str, Path], chunk_size: int, **kwargs
    ) -> None:
        """Write pandas DataFrame to Parquet file in chunks"""
        num_chunks = (len(df) + chunk_size - 1) // chunk_size
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(df))
            chunk = df.iloc[start_idx:end_idx]
            chunk_path = path / f"{i:06d}.parquet"
            self.write_parquet(chunk, chunk_path, **kwargs)

    def read_lines(self, path: Union[str, Path]) -> List[str]:
        with open(path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def read_file(self, path: Union[str, Path], **kwargs) -> Any:
        """Read file based on extension"""
        path = Path(path)
        extension = path.suffix.lower()

        if extension == ".csv":
            return self.read_csv(path, **kwargs)
        elif extension in [".parquet", ".pq"]:
            return self.read_parquet(path, **kwargs)
        else:
            raise ValueError(f"Unsupported file extension: {extension}")
