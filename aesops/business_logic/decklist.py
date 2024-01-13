from data_models.model_store import db
from data_models.players import Player
from aesops import app
from aesops.utility import get_cards
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
    for card in decklist_dict:
        card = card.strip()
        if card is None or card == "" or card in cardtypes:
            continue
        if card not in all_cards:
            if "(" in card and ")" in card:
                print(card)
                continue
            raise ValueError(f"{card} is not a valid card name")
        if all_cards[card]["type"] not in ordered_decklist.keys():
            ordered_decklist[all_cards[card]["type"]] = []
        ordered_decklist[all_cards[card]["type"]].append(
            {
                "name": card,
                "qty": int(decklist_dict[card]),
                "faction": all_cards[card]["faction"],
                "influence": int(all_cards[card]["influence"]),
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
