from data_models.model_store import db
from data_models.players import Player
from aesops import app
from aesops.utility import get_cards, convert_stipped_to_card
from data_models.users import User

"""
decklist_parser parses a decklist in one of two formats:
* The Jinteki.net format produced by NetrunnerDB, which is a list of cards like
```
1 Burner
3 Creative Commission
2 "Pretty" Mary Da Silva
...
```
* The output of copy/pasting a list from Jinteki.net, which is like the above but
also includes headings:
```
Event (14)
1  Burner 
3  Creative Commission
Resource (12)
2  "Pretty" Mary da Silva
...
```
This verifies that the list only contains valid Netrunner cards before saving.
It does _not_ verify deck legality.
"""
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
    # Create a dictionary mapping card name to its quantity.
    # Note that if a user provides a copy/paste deck from Jinteki.net, there
    # will be entries like "Agenda (5)" in their decklist which are converted
    # to "(5)": "Agenda" in this decklist_dict.
    # (Documenting this because it is very easy to miss.)
    decklist_dict = {
        decklist_cards.split(" ", 1)[1].strip(): decklist_cards.split(" ", 1)[0]
        for decklist_cards in decklist_cards
    }
    ordered_decklist = {}
    for card_name in decklist_dict:
        # decklist_dict[card_name] will break if card_name is changed, which
        # may be done on a later line if we convert the card name to its
        # formatted version (convert_stipped_to_card). Thus, we keep track of
        # the qty for later.
        qty = decklist_dict[card_name]
        # Note that entries like "Agenda (5)" will be "(5)": "Agenda", so have
        # qty = "Agenda". This check ignores lines like those.
        if qty in cardtypes:
            continue
        card_name = card_name.strip()
        if card_name not in all_cards:
            # If card_name has a formatted version, it returns that version.
            # This is used to deal with the difference between stripped_title
            # (used in the Jinteki.net export format expected by the parser)
            # and the formatted title on NetrunnerDB.
            # For example, convert_stipped_to_card('"Pretty" Mary Da Silva')
            # returns '“Pretty” Mary da Silva' (note the different quote marks).
            # If there is no such entry, return None.
            search_name = convert_stipped_to_card(card_name)
            if search_name is None:
                raise ValueError(f"{card_name} is not a valid card name")
            card_name = search_name
        if all_cards[card_name]["type"] not in ordered_decklist.keys():
            ordered_decklist[all_cards[card_name]["type"]] = []
        ordered_decklist[all_cards[card_name]["type"]].append(
            {
                "name": card_name,
                "qty": int(qty),
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
