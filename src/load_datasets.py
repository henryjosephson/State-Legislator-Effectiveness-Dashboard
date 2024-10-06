import argparse
import io
import logging
import os
from datetime import datetime

import pandas as pd
from legcop import LegiScan

from state_specific_data_downloads import NY_read_senate_api
from utils import get_legiscan_api_key, get_ny_senate_api_key

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_datasets(state, year):
    """
    checks if datasets are in memory. loads them in if they are, downloads them if they aren't.
    only takes a single (state,year) tuple at a time - loop over it if you want more than one.
    returns bills_df.
    """
    try:
        BASE_DIR = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    except NameError:
        BASE_DIR = os.path.dirname(os.path.dirname(os.getcwd()))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

    print(BASE_DIR, DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR)

    file_path = os.path.join(RAW_DATA_DIR, f"{state}-{year}.json")
    if os.path.exists(file_path):
        logger.info("Dataset already downloaded.")
        try:
            bills_df = pd.read_json(file_path).reset_index(drop=True)
            logger.info("Dataset loaded into memory.")
            return bills_df
        except FileNotFoundError:
            logger.info("File not found.")
            pass
        except Exception as e:
            logger.error(
                "Looks like your files are downloaded, but there's something wrong. "
                + "If you aren't sure what to do, deleting the files and running"
                + " the code again is usually a safe idea."
                + f"Error: {e}"
            )

    legis = LegiScan(get_legiscan_api_key.main())
    logger.info("Initialized LegiScan API")

    dataset_list = legis.get_dataset_list(state=state, year=year)

    ACCESS_KEY = dataset_list[0]["access_key"]
    SESSION_ID = dataset_list[0]["session_id"]

    del dataset_list

    logger.info(
        "Starting dataset download. This can take my laptop up to around 5 "
        + "minutes, especially for large datasets."
    )  # TODO: only download the missing datasets. looks like there's PHP to do
    # this at https://api.legiscan.com/docs/class-LegiScan_Worker.html
    dataset = legis.get_dataset(access_key=ACCESS_KEY, session_id=SESSION_ID)
    del ACCESS_KEY, SESSION_ID
    assert dataset["status"] == "OK"
    logger.info("Dataset download complete")

    logger.info("Starting pre-processing.")

    readable_dataset = legis.recode_zipfile(dataset)
    namelist = readable_dataset.namelist()

    list_of_bill_dfs = []

    for file in namelist:
        if "/bill/" in file:
            content = readable_dataset.read(file)
            list_of_bill_dfs.append(
                pd.read_json(io.StringIO(content.decode("UTF-8"))).T
            )
    logger.info(f"Processed {len(list_of_bill_dfs)} bills")

    del content, file, dataset, readable_dataset, namelist

    bills_df = pd.concat(list_of_bill_dfs)

    logger.info("Pre-processing complete. Saving to disk.")

    bills_df.reset_index(drop=True).to_json(file_path, index=False)
    logger.info(f"Saved processed data to {file_path}")

    return bills_df.reset_index(drop=True)


def main(state, year):
    try:
        BASE_DIR = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))
    except NameError:
        BASE_DIR = os.path.dirname(os.path.dirname(os.getcwd()))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")

    if state == "NY":
        outputs = []
        sen = None
        leg = None

        senate_api_data_path = os.path.join(RAW_DATA_DIR, f"NY-{year}-senate.json")
        if os.path.exists(senate_api_data_path):
            logger.info(f"found ny bills senate json for {year}")
            last_modified = datetime.fromtimestamp(
                os.path.getmtime(senate_api_data_path)
            )
            print(
                "You've already downloaded the bills from the NY Senate API"
                + f" for {year}. That file was last modified on "
                + str(last_modified)
                + ".\nDo you want to redownload?"
            )  # TODO: update with https://legislation.nysenate.gov/static/docs/html/bills.html#get-bill-updates
            redownload = input("y/[n]: ") or "n"
            if redownload.lower() == "y":
                logger.info("Redownloading")
                sen = NY_read_senate_api.main(year, get_ny_senate_api_key.main())
            logger.info("Using existing data.")
            sen = pd.read_json(senate_api_data_path)
        logger.info("Downloading NY bills from senate api.")

        legiscan_data_path = os.path.join(RAW_DATA_DIR, f"NY-{year}.json")
        if os.path.exists(legiscan_data_path):
            logger.info(f"found ny bills legiscan json for {year}")
            last_modified = datetime.fromtimestamp(os.path.getmtime(legiscan_data_path))
            print(
                "You've already downloaded the bills from LegiScan for "
                + f"{year}. That file was last modified on "
                + str(last_modified)
                + ".\nDo you want to redownload?"
            )
            redownload = input("y/[n]: ") or "n"
            if redownload.lower() == "y":
                logger.info("Redownloading")
                leg = load_datasets("NY", year)

        if isinstance(sen, pd.DataFrame):
            outputs.append(sen)
        else:
            sen = NY_read_senate_api.main(year, get_ny_senate_api_key.main())
            outputs.append(sen)

        if isinstance(leg, pd.DataFrame):
            outputs.append(leg)
        else:
            leg = load_datasets("NY", year)
            outputs.append(leg)

        return outputs

    logger.info("Downloading dataset from legiscan")
    return load_datasets(state, year)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--state", type=str, required=True, help="State abbreviation (e.g., 'CA')"
    )
    parser.add_argument("--year", type=int, required=True, help="Year (e.g., 2023)")
    args = parser.parse_args()
    main(args.state, args.year)
