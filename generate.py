#!/usr/bin/env python3
"""
OONI Zapret List Generator

Generates a list of blocked domains in Russia based on OONI data.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import urlencode

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def download_file(url: str, file_path: str, timeout: int = 30) -> bool:
    """
    Download file from URL and save to file_path.

    Args:
        url: URL to download from
        file_path: Local path to save the file
        timeout: Request timeout in seconds

    Returns:
        bool: True if download succeeded, False otherwise
    """
    try:
        logger.info(f"Downloading {url}...")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            file.write(response.content)
        logger.info(f"File downloaded successfully: {file_path}")
        return True

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while downloading {url}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error while downloading {url}")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {response.status_code} while downloading {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while downloading {url}: {e}")
        return False


def blocked_unique_domains(csv_path: str, txt_path: str) -> bool:
    """
    Process OONI CSV data to extract unique blocked domains.

    Args:
        csv_path: Path to input CSV file
        txt_path: Path to output TXT file

    Returns:
        bool: True if processing succeeded, False otherwise
    """
    try:
        if not os.path.exists(csv_path):
            logger.error(f"Input file not found: {csv_path}")
            return False

        logger.info(f"Processing domains from {csv_path}...")
        df = pd.read_csv(csv_path)

        # Filter out invalid domains (with multiple consecutive dots)
        pattern = r"^.*\.{2,}.*$"
        df = df[~df["domain"].str.match(pattern)]

        # Sort by measurement count and keep only first occurrence of each domain
        df = df.sort_values(by="measurement_count", ascending=False)
        df = df.drop_duplicates(subset="domain", keep="first")

        # Keep only domains where anomaly count > ok count
        df = df[df["anomaly_count"] > df["ok_count"]]

        # Save domains to text file
        df["domain"].to_csv(txt_path, index=False, header=False)
        logger.info(f"Processed domains saved to {txt_path}")
        return True

    except pd.errors.EmptyDataError:
        logger.error(f"Empty CSV file: {csv_path}")
        return False
    except pd.errors.ParserError as e:
        logger.error(f"Invalid CSV format in {csv_path}: {e}")
        return False
    except KeyError as e:
        logger.error(f"Missing required column in {csv_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while processing domains: {e}")
        return False


def cleanup_file(file_path: str) -> bool:
    """
    Delete file if it exists.

    Args:
        file_path: Path to file to delete

    Returns:
        bool: True if file was deleted or didn't exist, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
        else:
            logger.debug(f"File not found, skipping cleanup: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error cleaning up {file_path}: {e}")
        return False


def main(
    csv_file_path: str = "ooni_data.csv",
    txt_file_path: str = "domains.lst",
    days_back: int = 7,
) -> bool:
    """
    Main execution function.

    Args:
        csv_file_path: Path for downloaded CSV file
        txt_file_path: Path for output domains list
        output_file: Path for output IPs list (not currently used)
        days_back: Number of days to look back for data

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Calculate date range
        today = datetime.now()
        until_date = today.strftime("%Y-%m-%d")
        since_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # Build API URL with proper encoding
        base_url = "https://api.ooni.io/api/v1/aggregation"
        params = {
            "axis_y": "domain",
            "axis_x": "measurement_start_day",
            "probe_cc": "RU",
            "since": since_date,
            "until": until_date,
            "test_name": "web_connectivity",
            "time_grain": "day",
            "format": "CSV",
        }
        url = f"{base_url}?{urlencode(params)}"

        logger.info(f"Fetching data from {url}")

        # Download file
        if not download_file(url, csv_file_path):
            return False

        # Process domains
        if not blocked_unique_domains(csv_file_path, txt_file_path):
            return False

        # Cleanup temporary file
        cleanup_file(csv_file_path)

        logger.info("Generation completed successfully")
        return True

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")
        return False


if __name__ == "__main__":
    # Exit with appropriate code
    sys.exit(0 if main() else 1)
