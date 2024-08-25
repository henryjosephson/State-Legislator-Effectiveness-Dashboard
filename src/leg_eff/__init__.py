import gc
import io
import logging
import os
import sys

import pandas as pd
from legcop import LegiScan

sys.path.append(os.getcwd())
from leg_eff_secrets import LEGISCAN_API_KEY

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_datasets(state, year):
    """
    checks if datasets are in memory. loads them in if they are, downloads them if they aren't.
    only takes a single (state,year) tuple at a time - loop over it if you want more than one.
    returns a tuple of dfs: (bills, people, votes)
    """
    bools = []
    files_to_check = ["bills.csv", "people.csv", "votes.csv"]

    for f in files_to_check:
        bools.append(os.path.exists(f"../../data/raw/{state}-{year}-{f}"))

    if all(bools):
        logger.info("All datasets already downloaded.")
        return (
            pd.read_csv(f"../../data/raw/{state}-{year}-bills.csv"),
            pd.read_csv(f"../../data/raw/{state}-{year}-people.csv"),
            pd.read_csv(f"../../data/raw/{state}-{year}-votes.csv"),
        )

    logger.info(f"Dataset for {state}-{year} is either missing or incomplete.")

    legis = LegiScan(LEGISCAN_API_KEY)

    dataset_list = legis.get_dataset_list(state="NY", year=2021)

    ACCESS_KEY = dataset_list[0]["access_key"]
    SESSION_ID = dataset_list[0]["session_id"]

    del dataset_list

    logger.info(
        "Starting dataset download. This usually takes my laptop around 3-5 minutes."
    )  # TODO: only download the missing datasets
    dataset = legis.get_dataset(access_key=ACCESS_KEY, session_id=SESSION_ID)
    del ACCESS_KEY, SESSION_ID
    assert dataset["status"] == "OK"

    logger.info("Download complete. Starting pre-processing.")

    readable_dataset = legis.recode_zipfile(dataset)
    namelist = readable_dataset.namelist()

    list_of_bill_dfs = []
    list_of_people_dfs = []
    list_of_vote_dfs = []

    for file in namelist:
        content = readable_dataset.read(file)

        if "/bill/" in file:
            list_of_bill_dfs.append(
                pd.read_json(io.StringIO(content.decode("UTF-8"))).T
            )
        elif "/people/" in file:
            list_of_people_dfs.append(
                pd.read_json(io.StringIO(content.decode("UTF-8"))).T
            )
        elif "/vote/" in file:
            list_of_vote_dfs.append(
                pd.read_json(io.StringIO(content.decode("UTF-8"))).T
            )

    del content, file, dataset, readable_dataset, namelist

    bills_df = pd.concat(list_of_bill_dfs)
    people_df = pd.concat(list_of_people_dfs)
    votes_df = pd.concat(list_of_vote_dfs)

    logger.info("Pre-processing complete. Saving to disk.")

    bills_df.to_csv(f"../../data/raw/{state}-{year}-bills.csv", index=False)
    people_df.to_csv(f"../../data/raw/{state}-{year}-people.csv", index=False)
    votes_df.to_csv(f"../../data/raw/{state}-{year}-votes.csv", index=False)

    return (bills_df, people_df, votes_df)


def main():
    load_datasets(state="NY", year=2021)
    load_datasets(state="NY", year=2023)


if __name__ == "__main__":
    main()
