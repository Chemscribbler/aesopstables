import requests
import os
import datetime
from json import dump, load
from data_models.match import Match, MatchResult, convert_result_to_score
from data_models.players import Player
from data_models.tournaments import Tournament
import aesops.business_logic.players as p_logic
import aesops.business_logic.top_cut as tc_logic
import aesops.business_logic.tournament as t_logic
import aesops.cards as cards
import json
from decimal import Decimal
import unicodedata
import string

def get_corp_ids():
    return cards.data.corp_ids()

def get_runner_ids():
    return cards.data.runner_ids()

def render_side_bias(side_bal):
    if side_bal > 0:
        return f"Corp +{side_bal}"
    elif side_bal < 0:
        return f"Runner +{side_bal * -1}"
    return "Balanced"

def rank_tables(match_list: list[Match]):
    match_list.sort(key=lambda x: x.table_number or 1000)
    return match_list


def get_faction(corp_name: str):
    return cards.data.get_faction(corp_name)

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
        "date": t.date.strftime("%Y-%m-%d"),
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
            if match.concluded:
                match_list.append(
                    {
                        "tableNumber": match.table_number,
                        "player1": {
                            "id": match.corp_player.id,
                            "role": "corp",
                            "corpScore": convert_result_to_score(match.result, "corp"),
                            "runnerScore": None,
                        },
                        "player2": {
                            "id": (
                                match.runner_player.id if not match.is_bye else None
                            ),
                            "role": "runner",
                            "corpScore": None,
                            "runnerScore": (
                                convert_result_to_score(match.result, "runner")
                                if not match.is_bye
                                else None
                            ),
                        },
                        "intentionalDraw": match.result
                        == MatchResult.INTENTIONAL_DRAW.value,
                        "eliminationGame": False,
                    }
                )
        t_json["rounds"].append(match_list)
    if t.cut is not None:
        for rnd in range(1, t.cut.rnd + 1):
            match_list = []
            for match in tc_logic.get_round(t.cut, rnd):
                if match.concluded:
                    match_list.append(
                        {
                            "tableNumber": match.table_number,
                            "player1": {
                                "id": match.corp_player.player.id,
                                "role": "corp",
                                "corpScore": convert_result_to_score(
                                    match.result, "corp"
                                ),
                                "runnerScore": None,
                            },
                            "player2": {
                                "id": (match.runner_player.player.id),
                                "role": "runner",
                                "corpScore": None,
                                "runnerScore": convert_result_to_score(
                                    match.result, "runner"
                                ),
                            },
                            "intentionalDraw": False,
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
                "stripped_title": card["stripped_title"],
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


def convert_stipped_to_card(stripped_name):
    cards = get_cards()
    unaccent = remove_accents(stripped_name)
    for card in cards:
        if cards[card]["stripped_title"] == unaccent:
            return card
    return None


# Modified from https://stackoverflow.com/questions/8694815/removing-accent-and-special-characters
def remove_accents(data):
    return "".join(
        x for x in unicodedata.normalize("NFKD", data) if x in string.printable
    )
