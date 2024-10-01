import argparse
import json
import logging
import os
import shutil
import time

import pandas as pd
import requests

from utils import get_ny_senate_api_key

get_ny_senate_api_key.main()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_ny_senate_bills(year: int, api_key=None) -> None:
    if not isinstance(year, int) or year < 1000 or year > 9999:
        raise ValueError("Year must be a 4-digit integer.")

    # Set initial offset and API key
    offset = 1
    base_url = f"https://legislation.nysenate.gov/api/3/bills/{year}"
    logger.info(f"Fetching bills for {year} from {base_url}")

    if not api_key:
        api_key = get_ny_senate_api_key.main()

    # Ensure the save directory exists
    save_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "senate-api")
    )
    os.makedirs(save_dir, exist_ok=True)
    logger.info(f"Creating temporary directory {save_dir}")

    while True:
        # Construct the full URL
        url = f"{base_url}?key={api_key}&limit=1000&offset={offset}"

        # Create a filename for this batch
        filename = os.path.join(save_dir, f"bills_{year}_offset_{offset}.json")

        # Fetch the data
        response = requests.get(url)
        data = response.json()

        if not data["success"]:
            print("Failed to fetch data. Stopping.")
            return None

        # Check if the response is an empty list
        if data["responseType"] == "empty list":
            print("Received 'empty list' response. Stopping.")
            return None
        else:
            # Save the data to a file
            with open(filename, "w") as f:
                json.dump(data, f)
            logger.info(f"Saved {filename}")

            # Increase the offset for the next iteration
            offset += 1000

        # Optional: Add a small delay to avoid overwhelming the API
        time.sleep(0.5)


def merge_json_files(directory: str, output_file: str) -> None:
    """
    Merge all JSON files in the given directory into a single JSON file.

    Args:
        directory (str): The directory containing the JSON files.
        output_file (str): The path to the output file.
    """
    logger.info(f"Merging JSON files from {directory} into {output_file}")
    merged_data = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r") as f:
                data = json.load(f)["result"]["items"]
                merged_data.extend(data)

    with open(output_file, "w") as f:
        json.dump(merged_data, f, indent=4)
    print(f"Merged {len(merged_data)} bills into {output_file}")

    shutil.rmtree(directory)
    logger.info(f"Deleted temporary directory {directory}")


def main(year: int, api_key) -> pd.DataFrame:
    fetch_ny_senate_bills(year, api_key)
    merge_json_files(
        os.path.join("..", "data", "raw", "senate-api"),
        os.path.join("..", "data", "raw", f"NY-{year}-senate.json"),
    )
    bills_df = pd.read_json(
        os.path.join("..", "data", "raw", f"NY-{year}-senate.json")
    ).reset_index(drop=True)
    return bills_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, help="Year for which to fetch bills")
    parser.add_argument("--api_key", type=str, help="API key for LegiScan API")

    cwd = os.getcwd()

    try:
        args = parser.parse_args()
        year = args.year
        api_key = None
        if args.api_key:
            api_key = args.api_key
    except SystemExit:
        print("Usage: python NY_read_senate_api.py <year> [--api_key <api_key>]")
        raise

    os.chdir("/Users/henryjosephson/personal/Projects/leg_eff/src")
    main(year, api_key)
    os.chdir(cwd)
