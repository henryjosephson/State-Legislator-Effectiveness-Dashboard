"""
any errors are claude's, not mine.

I happen to be in France right now, and the NY Senate API won't take requests from
France. Luckily, they do take requests from UChicago's cs department's linux server,
so I just ran a version of this script there and scp'd the results back to my local
machine.
"""

import json
import os
import sys
import time
from typing import Optional

import requests

sys.path.append(os.getcwd())
try:
    from leg_eff_secrets import NYSENATE_API_KEY
except ImportError:
    NYSENATE_API_KEY = None


def fetch_ny_senate_bills(year: int, api_key: Optional[str] = None) -> None:
    if not isinstance(year, int) or year < 1000 or year > 9999:
        raise ValueError("Year must be a 4-digit integer.")

    # Set initial offset and API key
    offset = 1
    api_key = api_key or NYSENATE_API_KEY
    base_url = f"https://legislation.nysenate.gov/api/3/bills/{year}"

    # Ensure the save directory exists
    save_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "raw", "senate-api-raw"
        )
    )
    os.makedirs(save_dir, exist_ok=True)

    while True:
        # Construct the full URL
        url = f"{base_url}?key={api_key}&limit=1000&offset={offset}"

        # Create a filename for this batch
        filename = os.path.join(save_dir, f"bills_{year}_offset_{offset}.json")

        # Fetch the data
        response = requests.get(url)
        data = response.json()

        # Check if the response is an empty list
        if data.get("responseType") == "empty list":
            print("Received 'empty list' response. Stopping.")
            break
        else:
            # Save the data to a file
            with open(filename, "w") as f:
                json.dump(data, f)
            print(f"Saved {filename}")

            # Increase the offset for the next iteration
            offset += 1000

        # Optional: Add a small delay to avoid overwhelming the API
        time.sleep(1)

    print("Script completed. All bills have been fetched.")


def merge_json_files(directory: str, output_file: str) -> None:
    """
    Merge all JSON files in the given directory into a single JSON file.

    Args:
        directory (str): The directory containing the JSON files.
        output_file (str): The path to the output file.
    """
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ny_senate_bill_fetcher.py <year>")
        sys.exit(1)
    try:
        year = int(sys.argv[1])
        fetch_ny_senate_bills(year)
        merge_json_files(
            os.path.join("..", "..", "data", "raw", "senate-api"),
            os.path.join("..", "..", "data", "raw", "ny_senate_bills.json"),
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
