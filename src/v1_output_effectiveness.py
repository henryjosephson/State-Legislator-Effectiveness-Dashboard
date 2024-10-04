import logging
import os
import re

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main(state, year):
    if state == "NY":
        senate_path = [
            x
            for x in os.listdir("../data/raw")
            if ("senate" in x) & ("NY" in x) & (str(year) in x)
        ]

        try:
            senate = pd.read_json(os.path.join("..", "data", "raw", senate_path[0]))
            print("successfully loaded senate dataset")
        except (IndexError, FileNotFoundError) as e:
            print("did you download the senate data for this year?")
            print(e)

        try:
            legiscan = pd.read_json(
                os.path.join("..", "data", "raw", f"NY-{year}.json")
            )
            print("successfully loaded legiscan dataset")
        except FileNotFoundError as e:
            print("did you download the legiscan data for this year?")
            print(e)

        return senate, legiscan

    if state != "NY":
        raise ValueError(
            "It looks like we haven't implemented the state you're looking for yet."
        )


if __name__ == "__main__":
    main("NY", 2023)

print(__name__)
senate, legiscan = main("NY", 2023)


def remove_resolutions(df):
    return legiscan[
        df["bill_number"].str.startswith("A") | df["bill_number"].str.startswith("S")
    ].reset_index(drop=True)


def get_same_as(sasts_column: pd.Series) -> pd.Series:
    return sasts_column.apply(
        # check sast `type_id` == 1 for same_as.
        lambda x: x[0]["sast_bill_number"] if len(x) > 0 else None
    )


legiscan = remove_resolutions(legiscan)
logger.info("removed resolutions")

legiscan = legiscan.assign(SAME_AS=get_same_as(legiscan["sasts"]))
logger.info("Created SAME_AS column")


def expand_progress(progress_list):
    progress_dict = {
        0: "N/A Pre-filed or pre-introduction",
        1: "Introduced",
        2: "Engrossed",
        3: "Enrolled",
        4: "Passed",
        5: "Vetoed",
        6: "Failed",  # Limited support based on state
        7: "Override",
        8: "Chaptered",  # what bills are chaptered?
        9: "Refer",
        10: "Report Pass",
        11: "Report DNP",
        12: "Draft",
    }

    if len(progress_list) == 0:
        return []

    templist = []

    for update in progress_list:
        templist.append(progress_dict[update["event"]].lower())
    return templist


def expand_history(history_list):
    if len(history_list) == 0:
        return []

    templist = []

    for update in history_list:
        templist.append(update["action"].lower())
    return templist


def expand_votes(vote_list):
    if len(vote_list) == 0:
        return []

    templist = []

    for update in vote_list:
        templist.append(update["desc"].lower())
    return templist


legiscan["exp_progress"] = legiscan["progress"].apply(expand_progress)
legiscan["exp_history"] = legiscan["history"].apply(expand_history)
legiscan["exp_votes"] = legiscan["votes"].apply(expand_votes)
logger.info("Expanded progress, history, and votes columns")

legiscan["bill"] = legiscan["exp_progress"].apply(
    lambda progList: any(
        "introduced" in x.lower() if x is not None else False for x in progList
    ),
)
logger.info("Created BILL column")

# get AIC (check history?)
legiscan["aic"] = legiscan["exp_history"].apply(
    lambda historyList: (
        any(("committee" in event) for event in historyList)
        or any(("reading" in event) for event in historyList)
        or any(("third reading" in event) for event in historyList)
        or any(("report" in event) for event in historyList)
        or any(("amend and recommit" in event) for event in historyList)
        or any(("amend (t) and recommit" in event) for event in historyList)
        # which of the following count as actions in committee?
        # or any(("enacting clause stricken" in event) for event in historyList)
        # or any(("print number" in event) for event in historyList)
        # or any(("to attorney-general for opinion" in event) for event in historyList)
        # or any(("held for consideration" in event) for event in historyList)
    )
)
logger.info("Created AIC column")

# get PASS (check bill ID + history)
legiscan["chamber_of_origin"] = (
    legiscan["bill_number"].str[0].apply(lambda x: {"A": "assembly", "S": "senate"}[x])
)
logger.info("Created chamber_of_origin column")

# actually do 'passed_senate' and 'passed_assembly' columns so senators can get
# credit for bills passing senate but not for bills passing assembly
legiscan["pass"] = legiscan.apply(
    lambda row: f"passed {row['chamber_of_origin']}" in row["exp_history"],
    axis=1,
)
logger.info("Created pass column")

legiscan["pass_senate"] = (legiscan["chamber_of_origin"] == "senate") & (
    legiscan["pass"]
)
legiscan["pass_assembly"] = (legiscan["chamber_of_origin"] == "assembly") & (
    legiscan["pass"]
)
logger.info("Created pass_senate and pass_assembly columns")

legiscan["pass_other_house"] = legiscan.apply(
    lambda row: any(
        [
            [
                [
                    f"passed {x}"
                    for x in ["assembly", "senate"]
                    if x != row["chamber_of_origin"]
                ][0]
                in event
            ]
            for event in row["exp_history"]
        ]
    ),
    axis=1,
)
logger.info("Created pass_other_house column")


def standardize_bill_number_length(bill_number: str) -> str:
    bill_letter = bill_number[0]
    bill_number = bill_number[1:]

    if bool(re.search(r"[a-zA-Z]", bill_number)):
        bill_number = bill_number[:-1]

    if len(bill_number) < 5:
        bill_number = "0" * (5 - len(bill_number)) + bill_number
    return bill_letter.upper() + bill_number


legiscan["substituted_by"] = (
    # check -- does this give the same answer as using RAST?
    legiscan["exp_history"]
    .apply(
        lambda history_list: (
            history_list[-1].split()[-1]
            if any("substituted by" in x for x in history_list)
            else None
        )
    )
    .apply(lambda x: standardize_bill_number_length(x) if x is not None else None)
)
logger.info("Created substituted_by column")

# get LAW
legiscan["law"] = legiscan["exp_history"].apply(
    lambda history_list: any("signed" in x for x in history_list)
)

enacted_nos = legiscan[legiscan["law"]]["bill_number"]

legiscan["law"] = legiscan["exp_history"].apply(
    lambda history_list: any("signed" in x for x in history_list)
) | legiscan["substituted_by"].isin(enacted_nos)

logger.info("Created LAW column (which accounts for SUBSTITUTED_BY)")

senate["main_sponsor"] = [
    (
        d["member"]["fullName"]
        if bool(d["member"])
        else pd.Series(["budget", "rules", "redistricting"])
        .loc[[d["budget"], d["rules"], d["redistricting"]]]
        .iloc[0]
    )
    for d in senate["sponsor"]
]

legislator_dict = {}

for _, row in legiscan.iterrows():
    for spons in row["sponsors"]:
        legislator_dict[spons["name"]] = {
            "spons_house": spons["role"],
            "spons_party": spons["party"],
        }
# assumes that chamber and party are constant for an entire legislative session.
# can write more complicated error checking code if there's an update that
# doesn't match the existing party/house data. save the date of the bill
# that changes that, then have different responses dependint on whether
# the query happens before or after that date

bill_to_spons_df = pd.DataFrame(
    {
        "bill_number": senate["basePrintNo"].apply(standardize_bill_number_length),
        "main_sponsor": senate["main_sponsor"],
    }
)

bills = pd.merge(legiscan, bill_to_spons_df, on="bill_number", how="left")
logger.info("merged main sponsor information")
# TODO: lots of bills give credit to 'rules' this way -- check if there's a way to
# see if there's a way to get the actual sponsor name

effectiveness_df = bills.groupby(by="main_sponsor")[
    ["bill", "aic", "pass_other_house", "pass", "law"]
].sum()
effectiveness_df = effectiveness_df.merge(
    pd.DataFrame(legislator_dict).T,
    left_index=True,
    right_index=True,
)

logger.info("Created effectiveness dataframe")

effectiveness_df["score"] = effectiveness_df.apply(
    lambda row: sum(
        (
            row["bill"] / effectiveness_df["bill"].sum(),
            row["aic"] / effectiveness_df["aic"].sum(),
            row["pass"] / effectiveness_df["pass"].sum(),
            row["pass_other_house"] / effectiveness_df["pass_other_house"].sum(),
            row["law"] / effectiveness_df["law"].sum(),
        )
    )
    / 5,
    axis=1,
)
