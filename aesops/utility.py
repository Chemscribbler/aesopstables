import requests
import os
import datetime
from json import dump, load
from pairing.player import Player
from pairing.match import Match
import json


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
            os.remove("ids.json")
            return get_ids()
        # else, load the file
        with open("ids.json", "r") as f:
            ids = load(f)
    return ids


def get_corp_ids():
    corp_ids = set(id["name"] for id in get_ids() if id["side"] == "corp")
    corp_ids = list(corp_ids)
    corp_ids.sort()
    return corp_ids


def get_runner_ids():
    runner_ids = set(id["name"] for id in get_ids() if id["side"] == "runner")
    runner_ids = list(runner_ids)
    runner_ids.sort()
    return runner_ids


def display_side_bias(player: Player):
    if player.get_side_balance() > 0:
        return f"Corp +{player.get_side_balance()}"
    if player.get_side_balance() < 0:
        return f"Runner {player.get_side_balance()*-1}"
    return "Balanced"


def rank_tables(match_list: list[Match]):
    match_list.sort(key=lambda x: x.table_number or 1000)
    return match_list


def get_faction(corp_name: str):
    with open("ids.json") as f:
        ids = json.load(f)
        for id in ids:
            if id["name"] == corp_name:
                return id["faction"]


if __name__ == "__main__":
    print(get_corp_ids())
    print(get_runner_ids())
