#!/usr/bin/env python3
"""
OONI Zapret List Generator.

Generates a list of blocked domains in Russia based on OONI data.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

OONI_API_URL = "https://api.ooni.io/api/v1/aggregation"
DOWNLOAD_CHUNK_SIZE = 8192


def download_file(url: str, file_path: Path, timeout: int = 30) -> bool:
    """Download file from URL and save to file_path.

    Args:
        url: Source URL.
        file_path: Destination path.
        timeout: Request timeout in seconds.

    Returns:
        True on success, False on any failure.
    """
    try:
        logger.info("Downloading %s...", url)
        with requests.get(url, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    file.write(chunk)
        logger.info("File downloaded successfully: %s", file_path)
        return True
    except requests.exceptions.Timeout:
        logger.error("Timeout while downloading %s", url)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while downloading %s", url)
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error %s while downloading %s", e.response.status_code, url)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error while downloading %s: %s", url, e)
    return False


def filter_blocked_domains(df: pd.DataFrame) -> pd.DataFrame:
    """Filter OONI DataFrame to unique blocked domains.

    Pipeline:
        1. Drop rows with missing domain.
        2. Drop domains containing consecutive dots (invalid).
        3. Keep one row per domain with the highest measurement_count.
        4. Keep only domains where anomaly_count > ok_count.

    Args:
        df: Raw OONI DataFrame. Must contain columns: domain, measurement_count,
            anomaly_count, ok_count.

    Returns:
        Filtered DataFrame with a single column ``domain`` sorted in descending
        order of measurement_count (order of equal-count rows is unspecified).
    """
    df = df.dropna(subset=["domain"])
    df = df[~df["domain"].str.contains(r"\.{2,}", regex=True)]
    df = df.sort_values(by="measurement_count", ascending=False)
    df = df.drop_duplicates(subset="domain", keep="first")
    df = df[df["anomaly_count"] > df["ok_count"]]
    return df[["domain"]]


def blocked_unique_domains(csv_path: Path, txt_path: Path) -> bool:
    """Process OONI CSV data to extract unique blocked domains.

    Args:
        csv_path: Path to the OONI CSV export.
        txt_path: Destination path for the resulting domains list.

    Returns:
        True on success, False on any failure.
    """
    try:
        logger.info("Processing domains from %s...", csv_path)
        df = pd.read_csv(csv_path)
        filtered = filter_blocked_domains(df)
        filtered["domain"].to_csv(txt_path, index=False, header=False)
        logger.info("Processed domains saved to %s", txt_path)
        return True
    except pd.errors.EmptyDataError:
        logger.error("Empty CSV file: %s", csv_path)
    except pd.errors.ParserError as e:
        logger.error("Invalid CSV format in %s: %s", csv_path, e)
    except KeyError as e:
        logger.error("Missing required column in %s: %s", csv_path, e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error while processing domains: %s", e)
    return False


def build_ooni_url(days_back: int, *, now: datetime | None = None) -> str:
    """Build OONI API URL for the given date range.

    Args:
        days_back: How many days back from ``now`` to query.
        now: Reference timestamp (defaults to ``datetime.now()``). Exposed for
            deterministic testing.

    Returns:
        Fully-qualified aggregation API URL with query parameters.
    """
    today = now or datetime.now()
    params = {
        "axis_y": "domain",
        "axis_x": "measurement_start_day",
        "probe_cc": "RU",
        "since": (today - timedelta(days=days_back)).strftime("%Y-%m-%d"),
        "until": today.strftime("%Y-%m-%d"),
        "test_name": "web_connectivity",
        "time_grain": "day",
        "format": "CSV",
    }
    return f"{OONI_API_URL}?{urlencode(params)}"


def main(
    csv_file_path: Path = Path("ooni_data.csv"),
    txt_file_path: Path = Path("domains.lst"),
    days_back: int = 7,
) -> bool:
    """Generate blocked domains list from OONI data.

    Args:
        csv_file_path: Intermediate CSV path (deleted on success).
        txt_file_path: Output list path.
        days_back: Aggregation window in days.

    Returns:
        True on success, False on any failure.
    """
    try:
        url = build_ooni_url(days_back)
        logger.info("Fetching data from %s", url)

        if not download_file(url, csv_file_path):
            return False

        if not blocked_unique_domains(csv_file_path, txt_file_path):
            return False

        csv_file_path.unlink(missing_ok=True)
        logger.info("Generation completed successfully")
        return True
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error in main execution: %s", e)
    return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
