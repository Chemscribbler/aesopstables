from data_models.model_store import db
from data_models.players import Player
from aesops import app
from aesops.utility import get_cards, convert_stipped_to_card
from data_models.users import User


def decklist_parser(decklist: str):
    cardtypes = [
        "Event",
        "Hardware",
        "Resource",
        "Program",
        "Agenda",
        "Asset",
        "Upgrade",
        "Ice",
        "Operation",
    ]
    all_cards = get_cards()
    decklist = decklist.replace("●​", "")
    decklist = decklist.replace("•", "")
    decklist_cards = decklist.split("\n")
    print(decklist_cards)
    decklist_dict = {
        decklist_cards.split(" ", 1)[1].strip(): decklist_cards.split(" ", 1)[0]
        for decklist_cards in decklist_cards
    }
    ordered_decklist = {}
    for card_name in decklist_dict:
        card_name = card_name.strip()
        if card_name is None or card_name == "" or card_name in cardtypes:
            continue
        if card_name not in all_cards:
            search_name = convert_stipped_to_card(card_name)
            if search_name is None or ("(" in card_name and ")" in card_name):
                print(card_name)
                continue
            raise ValueError(f"{card_name} is not a valid card name")
        if all_cards[card_name]["type"] not in ordered_decklist.keys():
            ordered_decklist[all_cards[card_name]["type"]] = []
        ordered_decklist[all_cards[card_name]["type"]].append(
            {
                "name": card_name,
                "qty": int(decklist_dict[card_name]),
                "faction": all_cards[card_name]["faction"],
                "influence": int(all_cards[card_name]["influence"]),
            }
        )
    return ordered_decklist


def generate_decklist_html(decklist: dict, id_faction: str):
    decklist = decklist_parser(decklist)
    # sort ordered decklist keys
    ordered_decklist = dict(sorted(decklist.items(), key=lambda item: item[0]))
    # sort each list in ordered decklist
    for key in ordered_decklist:
        ordered_decklist[key] = sorted(
            ordered_decklist[key], key=lambda item: item["name"]
        )
    # create html table with columns: qty, name, influence
    text = f"<table class='table table-striped'><thead><tr><th>Count</th><th>Name</th><th>Influence</th></tr></thead>"
    for key in ordered_decklist:
        for card in ordered_decklist[key]:
            text += f"<tr><td>{card['qty']}</td><td>{card['name']}</td><td>{''.join(['•' for _ in range(card['qty'] * card['influence']) if card['faction'] != id_faction])}</td></tr>"

    return text + "</table>"
