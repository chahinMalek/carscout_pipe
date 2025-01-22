from abc import ABC, abstractmethod
from typing import List, Dict
from pathlib import Path
import pandas as pd

from src.config import ConfigManager
from src.io.file_service import LocalFileService


class BaseScraper(ABC):
    """Base class for all scrapers"""
    def __init__(self, config_manager: ConfigManager, file_service: LocalFileService):
        self.config_manager = config_manager
        self.file_service = file_service

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Main scraping method to be implemented by concrete scrapers"""
        pass

    def save_chunks(self, data: pd.DataFrame, output_dir: Path, chunk_size: int) -> None:
        """Common method for saving data in chunks to parquet files"""
        num_chunks = (len(data) + chunk_size - 1) // chunk_size
        print(f"Saving {num_chunks} chunks into {output_dir.resolve()}...")
        
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(data))
            chunk = data.iloc[start_idx:end_idx]
            
            chunk_path = output_dir / f"{i:04d}.parquet"
            self.file_service.write_parquet(chunk, chunk_path, index=False)

    def cleanup(self):
        """Clean up resources if needed"""
        pass 