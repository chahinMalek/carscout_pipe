import os
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, mock_open
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException

from carscout_pipe.exceptions import OlxPageNotFound
from carscout_pipe.main_functional import (
    get_config, setup_output_dir, load_brands, generate_listing_urls,
    scrape_vehicle, scrape_vehicles, save_batch, process_brand, main
)


class TestConfiguration:
    """Test configuration functions."""

    def test_get_config(self):
        """Test get_config returns expected config dictionary."""
        config = get_config()
        
        # Check required keys exist
        assert "brands_path" in config
        assert "request_min_delay_seconds" in config
        assert "request_max_delay_seconds" in config
        assert "wait_time_seconds" in config
        assert "url_template" in config
        assert "run_id" in config
        
        # Check types
        assert isinstance(config["brands_path"], str)
        assert isinstance(config["request_min_delay_seconds"], int)
        assert isinstance(config["request_max_delay_seconds"], int)
        assert isinstance(config["wait_time_seconds"], int)
        assert isinstance(config["url_template"], str)
        assert isinstance(config["run_id"], str)

    @patch("os.makedirs")
    def test_setup_output_dir(self, mock_makedirs):
        """Test setup_output_dir creates directory and returns correct paths."""
        run_id = "test-run-id"
        
        output_dir, output_template = setup_output_dir(run_id)
        
        # Check directory created
        mock_makedirs.assert_called_once_with(f"./data/output/{run_id}/", exist_ok=True)
        
        # Check return values
        assert output_dir == f"./data/output/{run_id}/"
        assert "{idx:08}" in output_template
        assert output_dir in output_template

    @patch("pandas.read_csv")
    def test_load_brands(self, mock_read_csv):
        """Test load_brands reads CSV file and returns records."""
        # Setup mock
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [{"brand_id": 1}, {"brand_id": 2}]
        mock_read_csv.return_value = mock_df
        
        # Call function
        brands = load_brands("path/to/brands.csv")
        
        # Assertions
        mock_read_csv.assert_called_once_with("path/to/brands.csv")
        mock_df.to_dict.assert_called_once_with(orient="records")
        assert len(brands) == 2
        assert brands[0]["brand_id"] == 1
        assert brands[1]["brand_id"] == 2


class TestScrapingFunctions:
    """Test core scraping functions."""

    @patch("carscout_pipe.main_functional.get_page_source")
    @patch("carscout_pipe.main_functional.get_next_page")
    @patch("carscout_pipe.main_functional.Selector")
    @patch("carscout_pipe.main_functional.random.shuffle")
    def test_generate_listing_urls_success(self, mock_shuffle, mock_selector_class, mock_get_next_page, mock_get_page_source):
        """Test generate_listing_urls yields expected URLs and handles pagination."""
        # Setup mocks
        driver = MagicMock()
        mock_page_source = "<html><body>Test</body></html>"
        mock_get_page_source.return_value = mock_page_source
        
        # Disable shuffling by making shuffle a no-op
        mock_shuffle.side_effect = lambda x: None
        
        # Mock two pages of results, then no next page
        mock_get_next_page.side_effect = ["2", None]
        
        # Setup mock selector to return listing URLs
        mock_selector = MagicMock()
        mock_selector_class.return_value = mock_selector
        
        # Mock xpath to return URL suffixes
        mock_xpath = MagicMock()
        mock_selector.xpath.return_value = mock_xpath
        mock_xpath.getall.return_value = ["/item/123", "/item/456"]
        
        # Call generator and collect results
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        results = list(generate_listing_urls(
            driver, 
            brand_id=1, 
            url_template="http://example.com/{brand_id}/{page}", 
            request_config=request_config
        ))
        
        # Assertions
        assert len(results) == 2  # Two pages of results
        
        # Check first page
        page1_url, page1_listings = results[0]
        assert page1_url == "http://example.com/1/1"
        
        # Use set comparison instead of list comparison to ignore order
        assert set(page1_listings) == {"https://olx.ba/item/123", "https://olx.ba/item/456"}
        
        # Check second page
        page2_url, page2_listings = results[1]
        assert page2_url == "http://example.com/1/2"

        # Again, use set comparison instead of list comparison to ignore order
        assert set(page2_listings) == {"https://olx.ba/item/123", "https://olx.ba/item/456"}

    @patch("carscout_pipe.main_functional.get_page_source")
    def test_generate_listing_urls_timeout(self, mock_get_page_source):
        """Test generate_listing_urls handles timeout exception."""
        # Setup mocks
        driver = MagicMock()
        mock_get_page_source.side_effect = TimeoutException("Timeout")
        
        # Call generator and collect results
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        results = list(generate_listing_urls(
            driver, 
            brand_id=1, 
            url_template="http://example.com/{brand_id}/{page}", 
            request_config=request_config
        ))
        
        # Assertions - should yield nothing after exception
        assert len(results) == 0

    @patch("carscout_pipe.main_functional.get_page_source")
    def test_generate_listing_urls_not_found(self, mock_get_page_source):
        """Test generate_listing_urls handles page not found exception."""
        # Setup mocks
        driver = MagicMock()
        mock_get_page_source.side_effect = OlxPageNotFound("http://example.com/1/1")
        
        # Call generator and collect results
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        results = list(generate_listing_urls(
            driver, 
            brand_id=1, 
            url_template="http://example.com/{brand_id}/{page}", 
            request_config=request_config
        ))
        
        # Assertions - should yield nothing after exception
        assert len(results) == 0

    @patch("carscout_pipe.main_functional.get_page_source")
    @patch("carscout_pipe.main_functional.parse_vehicle_info")
    @patch("carscout_pipe.main_functional.Selector")
    def test_scrape_vehicle_success(self, mock_selector_class, mock_parse_vehicle_info, mock_get_page_source):
        """Test scrape_vehicle successfully scrapes a vehicle."""
        # Setup mocks
        driver = MagicMock()
        mock_page_source = "<html><body>Test</body></html>"
        mock_get_page_source.return_value = mock_page_source
        
        # Mock selector
        mock_selector = MagicMock()
        mock_selector_class.return_value = mock_selector
        
        # Mock vehicle info
        mock_parse_vehicle_info.return_value = {"make": "Toyota", "model": "Corolla"}
        
        # Call function
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        vehicle = scrape_vehicle(
            driver, 
            "http://example.com/vehicle/123", 
            request_config, 
            "test-run-id"
        )
        
        # Assertions
        assert vehicle["make"] == "Toyota"
        assert vehicle["model"] == "Corolla"
        assert vehicle["url"] == "http://example.com/vehicle/123"
        assert "scraped_at" in vehicle
        assert vehicle["run_id"] == "test-run-id"

    @patch("carscout_pipe.main_functional.get_page_source")
    def test_scrape_vehicle_timeout(self, mock_get_page_source):
        """Test scrape_vehicle handles timeout exception."""
        # Setup mocks
        driver = MagicMock()
        mock_get_page_source.side_effect = TimeoutException("Timeout")
        
        # Call function
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        vehicle = scrape_vehicle(
            driver, 
            "http://example.com/vehicle/123", 
            request_config, 
            "test-run-id"
        )
        
        # Assertions - should return None on error
        assert vehicle is None

    def test_scrape_vehicles_empty(self):
        """Test scrape_vehicles with empty list."""
        driver = MagicMock()
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        vehicles = scrape_vehicles(driver, [], request_config, "test-run-id")
        assert vehicles == []

    @patch("carscout_pipe.main_functional.scrape_vehicle")
    def test_scrape_vehicles_with_listings(self, mock_scrape_vehicle):
        """Test scrape_vehicles processes all listing URLs."""
        # Setup mocks
        driver = MagicMock()
        
        # Mock vehicle scraping - first one succeeds, second fails
        mock_scrape_vehicle.side_effect = [
            {"make": "Toyota", "model": "Corolla"},
            None
        ]
        
        # Call function with two listings
        request_config = {"min_delay": 1, "max_delay": 2, "timeout": 5}
        with patch("tqdm.tqdm"):  # Mock tqdm to avoid progress bar
            vehicles = scrape_vehicles(
                driver, 
                ["http://example.com/vehicle/1", "http://example.com/vehicle/2"], 
                request_config, 
                "test-run-id"
            )
        
        # Assertions - should include only the successful vehicle
        assert len(vehicles) == 1
        assert vehicles[0]["make"] == "Toyota"
        assert vehicles[0]["model"] == "Corolla"


class TestDataManagement:
    """Test data saving and processing functions."""

    @patch("pandas.DataFrame.to_csv")
    def test_save_batch_success(self, mock_to_csv):
        """Test save_batch successfully saves data and increments index."""
        vehicles = [
            {"make": "Toyota", "model": "Corolla"},
            {"make": "Honda", "model": "Civic"}
        ]
        
        output_template = "/path/to/output/part_{idx:08}.csv"
        next_idx = save_batch(vehicles, output_template, 5)
        
        # Assertions
        mock_to_csv.assert_called_once_with("/path/to/output/part_00000005.csv", index=False)
        assert next_idx == 6  # Should increment

    @patch("pandas.DataFrame.to_csv")
    def test_save_batch_empty(self, mock_to_csv):
        """Test save_batch with empty data doesn't save and returns same index."""
        output_template = "/path/to/output/part_{idx:08}.csv"
        next_idx = save_batch([], output_template, 5)
        
        # Assertions
        mock_to_csv.assert_not_called()
        assert next_idx == 5  # Should not increment

    @patch("pandas.DataFrame.to_csv")
    def test_save_batch_error(self, mock_to_csv):
        """Test save_batch handles errors and returns same index."""
        vehicles = [{"make": "Toyota", "model": "Corolla"}]
        
        # Mock to_csv to raise an exception
        mock_to_csv.side_effect = Exception("Save error")
        
        output_template = "/path/to/output/part_{idx:08}.csv"
        next_idx = save_batch(vehicles, output_template, 5)
        
        # Assertions - should return same index on error
        assert next_idx == 5

    @patch("carscout_pipe.main_functional.generate_listing_urls")
    @patch("carscout_pipe.main_functional.scrape_vehicles")
    @patch("carscout_pipe.main_functional.save_batch")
    def test_process_brand(self, mock_save_batch, mock_scrape_vehicles, mock_generate_listing_urls):
        """Test process_brand processes all pages for a brand."""
        # Setup mocks
        driver = MagicMock()
        
        # Mock two pages of results
        mock_generate_listing_urls.return_value = [
            ("http://example.com/1/1", ["http://example.com/vehicle/1"]),
            ("http://example.com/1/2", ["http://example.com/vehicle/2"])
        ]
        
        # Mock scraping results
        mock_scrape_vehicles.side_effect = [
            [{"make": "Toyota", "model": "Corolla"}],
            [{"make": "Honda", "model": "Civic"}]
        ]
        
        # Mock save batch - increment index each time
        mock_save_batch.side_effect = lambda vehicles, template, idx: idx + 1
        
        # Call function
        brand_data = {"brand_id": 1}
        config = {
            "request_min_delay_seconds": 1,
            "request_max_delay_seconds": 2,
            "wait_time_seconds": 5,
            "url_template": "http://example.com/{brand_id}/{page}",
            "run_id": "test-run-id"
        }
        output_template = "/path/to/output/part_{idx:08}.csv"
        
        final_idx = process_brand(driver, brand_data, config, output_template, 0)
        
        # Assertions
        assert mock_generate_listing_urls.call_count == 1
        assert mock_scrape_vehicles.call_count == 2
        assert mock_save_batch.call_count == 2
        assert final_idx == 2  # Should have incremented twice


class TestMainFunction:
    """Test the main entry point function."""

    @patch("carscout_pipe.main_functional.get_config")
    @patch("carscout_pipe.main_functional.setup_output_dir")
    @patch("carscout_pipe.main_functional.load_brands")
    @patch("carscout_pipe.main_functional.init_driver")
    @patch("carscout_pipe.main_functional.process_brand")
    def test_main_success(self, mock_process_brand, mock_init_driver, 
                         mock_load_brands, mock_setup_output_dir, mock_get_config):
        """Test main function orchestrates the process successfully."""
        # Setup mocks
        mock_get_config.return_value = {
            "brands_path": "path/to/brands.csv",
            "request_min_delay_seconds": 1,
            "request_max_delay_seconds": 2,
            "wait_time_seconds": 5,
            "url_template": "http://example.com/{brand_id}/{page}",
            "run_id": "test-run-id"
        }
        
        mock_setup_output_dir.return_value = ("/path/to/output/", "/path/to/output/part_{idx:08}.csv")
        mock_load_brands.return_value = [{"brand_id": 1}, {"brand_id": 2}]
        
        driver_mock = MagicMock()
        mock_init_driver.return_value = driver_mock
        
        # Mock process_brand to return incremented index
        mock_process_brand.side_effect = lambda driver, brand, config, template, idx: idx + 1
        
        # Call function
        main()
        
        # Assertions
        mock_get_config.assert_called_once()
        mock_setup_output_dir.assert_called_once_with("test-run-id")
        mock_load_brands.assert_called_once_with("path/to/brands.csv")
        mock_init_driver.assert_called_once()
        
        # Should call process_brand twice (once for each brand)
        assert mock_process_brand.call_count == 2
        
        # Check final calls were made with correct indices
        _, _, _, _, idx1 = mock_process_brand.call_args_list[0][0]
        _, _, _, _, idx2 = mock_process_brand.call_args_list[1][0]
        assert idx1 == 0
        assert idx2 == 1
        
        # Check driver cleanup
        driver_mock.quit.assert_called_once()

    @patch("carscout_pipe.main_functional.get_config")
    @patch("carscout_pipe.main_functional.setup_output_dir")
    @patch("carscout_pipe.main_functional.load_brands")
    @patch("carscout_pipe.main_functional.init_driver")
    @patch("sys.exit")
    def test_main_driver_init_failure(self, mock_exit, mock_init_driver, 
                                    mock_load_brands, mock_setup_output_dir, mock_get_config):
        """Test main function handles WebDriver initialization failure."""
        # Setup mocks
        mock_get_config.return_value = {
            "brands_path": "path/to/brands.csv",
            "request_min_delay_seconds": 1,
            "request_max_delay_seconds": 2,
            "wait_time_seconds": 5,
            "url_template": "http://example.com/{brand_id}/{page}",
            "run_id": "test-run-id"
        }
        
        mock_setup_output_dir.return_value = ("/path/to/output/", "/path/to/output/part_{idx:08}.csv")
        mock_load_brands.return_value = [{"brand_id": 1}, {"brand_id": 2}]
        
        # Mock driver initialization to fail
        mock_init_driver.side_effect = WebDriverException("Failed to initialize")
        
        # Call function
        main()
        
        # Assertions - should exit with code 1
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main() 