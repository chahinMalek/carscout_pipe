import os
import tempfile

import pandas as pd
import pytest

from infra.factory.logger import LoggerFactory
from infra.io.file_service import LocalFileService


@pytest.mark.integration
class TestLocalFileService:
    @pytest.fixture
    def logger_factory(self):
        return LoggerFactory(format="%(name)s - %(message)s", log_level=20)

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def file_service(self, temp_dir, logger_factory):
        return LocalFileService(basedir=temp_dir, logger_factory=logger_factory)

    @pytest.fixture
    def sample_csv_file(self, temp_dir):
        data = {
            "name": ["Toyota", "Honda", "Mercedes"],
            "country": ["Japan", "Japan", "Germany"],
            "year": [1937, 1948, 1926],
        }
        df = pd.DataFrame(data)
        fpath = "brands.csv"
        csv_path = os.path.join(temp_dir, fpath)
        df.to_csv(csv_path, index=False)
        return fpath

    def test_read_csv_success(self, file_service, sample_csv_file):
        df = file_service.read_csv(sample_csv_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["name", "country", "year"]
        assert df.iloc[0]["name"] == "Toyota"
        assert df.iloc[0]["country"] == "Japan"
        assert df.iloc[0]["year"] == 1937

    def test_read_csv_file_not_exists(self, file_service):
        with pytest.raises(FileNotFoundError):
            file_service.read_csv("not_exists.csv")

    def test_file_exists(self, file_service, sample_csv_file, temp_dir):
        # existing file
        assert file_service.file_exists(sample_csv_file) is True
        # non-existing file
        assert file_service.file_exists("not_exists.csv") is False
        # returns False for directories
        subdir = os.path.join(temp_dir, "testdir")
        os.makedirs(subdir, exist_ok=True)
        assert file_service.file_exists("testdir") is False
