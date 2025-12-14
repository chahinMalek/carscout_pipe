import pandas as pd

from core.entities.brand import Brand
from infra.interfaces.file_service import FileService


class BrandService:
    def __init__(self, file_service: FileService, brands_path: str):
        self._file_service = file_service
        self._brands_path = brands_path
        self._brands_df: pd.DataFrame | None = None

    def read_brands(self) -> pd.DataFrame:
        if self._brands_df is None:
            self._brands_df = self._file_service.read_csv(self._brands_path)
        return self._brands_df

    def get_brands(self) -> pd.DataFrame:
        if self._brands_df is None:
            raise RuntimeError(
                "Brands not loaded. Call read_brands() first or ensure container is initialized."
            )
        return self._brands_df

    def load_brands(self) -> list[Brand]:
        df = self.get_brands()
        brands = [
            Brand(id=str(row["id"]), name=str(row["name"]), slug=str(row["slug"]))
            for _, row in df.iterrows()
        ]
        return brands

    def get_brand_by_id(self, brand_id: str) -> Brand | None:
        df = self.get_brands()
        row = df[df["id"] == brand_id]
        if row.empty:
            return None
        row = row.iloc[0]
        return Brand(id=str(row["id"]), name=str(row["name"]), slug=str(row["slug"]))

    def get_brand_by_slug(self, slug: str) -> Brand | None:
        df = self.get_brands()
        row = df[df["slug"] == slug]
        if row.empty:
            return None
        row = row.iloc[0]
        return Brand(id=str(row["id"]), name=str(row["name"]), slug=str(row["slug"]))
