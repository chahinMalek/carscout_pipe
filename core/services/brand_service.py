import pandas as pd

from core.entities.brand import Brand
from infra.interfaces.file_service import FileService


class BrandService:

    def __init__(self, file_service: FileService, brands_path: str):
        self._file_service = file_service
        self._brands_path = brands_path
    
    def read_brands(self) -> pd.DataFrame:
        return self._file_service.read_csv(self._brands_path)

    def load_brands(self) -> list[Brand]:
        df = self.read_brands()
        brands = [
            Brand(
                id=str(row['id']),
                name=str(row['name']),
                slug=str(row['slug'])
            )
            for _, row in df.iterrows()
        ]
        return brands
