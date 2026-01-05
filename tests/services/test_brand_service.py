from unittest.mock import MagicMock

import pandas as pd
import pytest

from core.services.brand_service import BrandService


class TestBrandService:
    @pytest.fixture
    def mock_file_service(self):
        return MagicMock()

    @pytest.fixture
    def brand_service(self, mock_file_service):
        return BrandService(mock_file_service, "brands.csv")

    def test_read_brands(self, brand_service, mock_file_service):
        df = pd.DataFrame([{"id": "1", "name": "Audi", "slug": "audi"}])
        mock_file_service.read_csv.return_value = df

        result = brand_service.read_brands()

        assert result.equals(df)
        mock_file_service.read_csv.assert_called_once_with("brands.csv")

    def test_get_brands_not_loaded(self, brand_service):
        with pytest.raises(RuntimeError, match="Brands not loaded"):
            brand_service.get_brands()

    def test_load_brands(self, brand_service, mock_file_service):
        df = pd.DataFrame(
            [{"id": "1", "name": "Audi", "slug": "audi"}, {"id": "2", "name": "BMW", "slug": "bmw"}]
        )
        mock_file_service.read_csv.return_value = df
        brand_service.read_brands()

        brands = brand_service.load_brands()

        assert len(brands) == 2
        assert brands[0].name == "Audi"
        assert brands[1].slug == "bmw"

    def test_get_brand_by_id(self, brand_service, mock_file_service):
        df = pd.DataFrame([{"id": "1", "name": "Audi", "slug": "audi"}])
        mock_file_service.read_csv.return_value = df
        brand_service.read_brands()

        brand = brand_service.get_brand_by_id("1")
        assert brand.name == "Audi"

        brand_none = brand_service.get_brand_by_id("2")
        assert brand_none is None

    def test_get_brand_by_slug(self, brand_service, mock_file_service):
        df = pd.DataFrame([{"id": "1", "name": "Audi", "slug": "audi"}])
        mock_file_service.read_csv.return_value = df
        brand_service.read_brands()

        brand = brand_service.get_brand_by_slug("audi")
        assert brand.id == "1"

        brand_none = brand_service.get_brand_by_slug("bmw")
        assert brand_none is None
