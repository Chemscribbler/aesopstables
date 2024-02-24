import requests
import os
import datetime
from json import dump, load
from data_models.match import Match, MatchResult
from data_models.players import Player
from data_models.tournaments import Tournament
import aesops.business_logic.players as p_logic
import aesops.business_logic.top_cut as tc_logic
import aesops.business_logic.tournament as t_logic
import json
from decimal import Decimal


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
    side_bal = p_logic.get_side_balance(player)
    if side_bal > 0:
        return f"Corp +{side_bal}"
    elif side_bal < 0:
        return f"Runner +{side_bal * -1}"
    return "Balanced"


def rank_tables(match_list: list[Match]):
    match_list.sort(key=lambda x: x.table_number or 1000)
    return match_list


def get_faction(corp_name: str):

    ids = get_ids()
    for id in ids:
        if id["name"] == corp_name:
            return id["faction"]


def get_faction_color(faction: str):

    colors = {
        "anarch": "orangered",
        "criminal": "royalblue",
        "shaper": "limegreen",
        "neutral-runner": "gray",
        "haas-bioroid": "blueviolet",
        "jinteki": "crimson",
        "nbn": "#ffc107",
        "weyland-consortium": "darkgreen",
        "neutral-corp": "gray",
    }
    if faction not in colors:
        return "gray"
    return colors[faction]


def format_results(match: Match):
    if match.result is None:
        return ""
    if match.result == MatchResult.CORP_WIN.value:
        return "3 - 0"
    if match.result == MatchResult.RUNNER_WIN.value:
        return "0 - 3"
    if match.result in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value]:
        return "1 - 1"


def get_json(tid):
    t = Tournament.query.get(tid)
    t_json = {
        "name": t.name,
        "cutToTop": t.cut.num_players if t.cut is not None else 0,
        "preliminaryRounds": t.current_round,
        "players": [],
        "eliminationPlayers": [],
        "rounds": [],
        "uploadedFrom": "AesopsTables",
        "links": [
            {
                "rel": "schemaderivedfrom",
                "href": "http://steffens.org/nrtm/nrtm-schema.json",
            },
            {"rel": "uploadedfrom", "href": "https://github.com/Chemscribbler/sass"},
        ],
    }

    for i, player in enumerate(t_logic.rank_players(t)):
        t_json["players"].append(
            {
                "id": player.id,
                "name": player.name,
                "rank": i + 1,
                "corpIdentity": player.corp,
                "runnerIdentity": player.runner,
                "matchPoints": player.score,
                "strengthOfSchedule": player.sos,
                "extendedStrengthOfSchedule": player.esos,
                "sideBalance": p_logic.get_side_balance(player),
            }
        )
    if t.cut is not None:
        for i, player in enumerate(tc_logic.get_standings(t.cut)["ranked_players"]):
            t_json["eliminationPlayers"].append(
                {
                    "id": player.player.id,
                    "name": player.player.name,
                    "rank": i + 1,
                    "seed": player.seed,
                }
            )
    for rnd in range(1, t.current_round + 1):
        match_list = []
        for match in t_logic.get_round(t, rnd):
            match_list.append(
                {
                    "tableNumber": match.table_number,
                    "corpPlayer": match.corp_player.id,
                    "runnerPlayer": (
                        match.runner_player.id if not match.is_bye else "(BYE)"
                    ),
                    "corpIdentity": match.corp_player.corp,
                    "runnerIdentity": (
                        match.runner_player.runner if not match.is_bye else ""
                    ),
                    "corpScore": format_results(match).split(" - ")[0],
                    "runnerScore": format_results(match).split(" - ")[1],
                }
            )
        t_json["rounds"].append(match_list)
    if t.cut is not None:
        for rnd in range(1, t.cut.rnd + 1):
            match_list = []
            for match in tc_logic.get_round(t.cut, rnd):
                corp_id = match.corp_player.player.id
                runner_id = match.runner_player.player.id
                match_list.append(
                    {
                        "tableNumber": match.table_number,
                        "corpPlayer": corp_id,
                        "runnerPlayer": runner_id,
                        "winner_id": (
                            corp_id
                            if match.result == MatchResult.CORP_WIN.value
                            else runner_id
                        ),
                        "loser_id": (
                            runner_id
                            if match.result == MatchResult.CORP_WIN.value
                            else corp_id
                        ),
                        "eliminationGame": True,
                    }
                )
            t_json["rounds"].append(match_list)

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Decimal):
                return float(o)
            return super(DecimalEncoder, self).default(o)

    json_data = json.dumps(t_json, cls=DecimalEncoder)
    return json_data


def get_cards():
    if not os.path.exists("cards.json"):
        all_cards = requests.get(
            "https://netrunnerdb.com/api/2.0/public/cards", timeout=15
        )
        cards = {
            card["title"]: {
                "side": card["side_code"],
                "faction": card["faction_code"],
                "name": card["title"],
                "type": card["type_code"],
                "influence": card["faction_cost"],
            }
            for card in all_cards.json()["data"]
            if card["type_code"] != "identity"
        }
        with open("cards.json", "w") as f:
            dump(cards, f)
    else:
        cards = []
        # If the file is older than a day, delete it and get a new one
        if os.path.getmtime("cards.json") < datetime.datetime.now().timestamp() - (
            60 * 60 * 24
        ):
            os.remove("cards.json")
            return get_cards()
        # else, load the file
        with open("cards.json", "r") as f:
            cards = load(f)
    return cards
