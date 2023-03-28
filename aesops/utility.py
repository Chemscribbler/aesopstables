import requests
import os
import datetime
from json import dump, load


def get_ids():
    # if the file doesn't exist, get it from the NetrunnerDB API (2.0)
    if not os.path.exists("ids.json"):
        all_cards = requests.get(
            "https://netrunnerdb.com/api/2.0/public/cards", timeout=5
        )
        ids = [
            {
                "side": card["side_code"],
                "faction": card["faction_code"],
                "name": card["title"],
            }
            for card in all_cards.json()["data"]
            if card["type_code"] == "identity"
        ]
        with open("ids.json", "w") as f:
            dump(ids, f)
    else:
        ids = []
        # If the file is older than a day, delete it and get a new one
        if os.path.getmtime("ids.json") < datetime.datetime.now().timestamp() - (
            60 * 60 * 24
        ):
            os.path.remove("ids.json")
            return get_ids()
        # else, load the file
        with open("ids.json", "r") as f:
            ids = load(f)
    return ids


def get_corp_ids():
    return [id["name"] for id in get_ids() if id["side"] == "corp"]


def get_runner_ids():
    return [id["name"] for id in get_ids() if id["side"] == "runner"]


if __name__ == "__main__":
    print(get_corp_ids())
    print(get_runner_ids())
