import os
from datetime import datetime, timedelta

import pandas as pd
import requests


def download_file(url, file_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"File was successfully downloaded and saved as {file_path}")
        else:
            print("Failed to download the file.")
    except Exception as e:
        print(f"An error occurred while downloading the file: {e}")


def blocked_unique_domains(csv_path, txt_path):
    try:
        df = pd.read_csv(csv_path)
        pattern = r"^.*\.{2,}.*$"  # Pattern to match incorrect domains
        df = df[~df["domain"].str.match(pattern)].sort_values(
            by="measurement_count", ascending=False
        )
        df = df.drop_duplicates(subset="domain", keep="first")
        df = df[df["anomaly_count"] > df["ok_count"]]
        df["domain"].to_csv(txt_path, index=False, header=False)
        print(f"Processed domains have been saved to {txt_path}")
    except Exception as e:
        print(f"An error occurred while processing the domains: {e}")


def delete_ooni_file(csv_file_path):
    try:
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            print("ooni file has been deleted")
        else:
            print("ooni file not found")
    except Exception as e:
        print(f"An error occurred while deleting the file: {e}")


# Calculate dates
today = datetime.now()
until_date = today.strftime("%Y-%m-%d")
since_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

# Construct the URL
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
url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

# File paths
csv_file_path = "ooni_data.csv"
txt_file_path = "domains.lst"
output_file = "ips.lst"

# Download file
download_file(url, csv_file_path)

# Process CSV to TXT
blocked_unique_domains(csv_file_path, txt_file_path)

# Delete CSV
delete_ooni_file(csv_file_path)
