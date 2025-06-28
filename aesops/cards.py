import requests
from datetime import datetime
from threading import Thread
from time import sleep
import logging
import json
import os

logger = logging.getLogger(__name__)


# This class might seem a bit redundant, just wrapping the inner workings of the Cards class,
# however keeping it nested like this lets us refresh the data in the background and swap the
# inner reference out in 1 go, avoiding threading related issues
class CardData:
    def __init__(self, ids, name_to_code, runner_ids, corp_ids):
        self.ids = ids
        self.name_to_code = name_to_code
        self.runner_ids = runner_ids
        self.corp_ids = corp_ids

    def get_faction(self, name: str):
        """Given the card name, return the faction it belongs to"""
        if name is not None:
            card_code = self.name_to_code[name]
            if card_code is not None:
                return self.ids[card_code]["faction"]

        return None

    def corp_ids(self):
        return self.corp_ids

    def runner_ids(self):
        return self.runner_ids

    def save(self):
        with open("card-data.json", "w") as f:
            json.dump(self.__dict__, f)

    def load(self):
        """If we have a copy of the cards on disk, load it"""
        if os.path.exists("card-data.json"):
            with open("card-data.json", "r") as f:
                self.__dict__ = json.load(f)


class Cards:
    """
    An in memory data store for information about cards

    Stores data in a quickly accessible format so that we can efficiently look up data to
    render user interfaces.

    Includes a mechanism for refreshing the data from the Netrunner DB API
    """

    def __init__(self):
        """Construct the data store and populate with the most recent data"""
        # Load what we have on disk in case we can't talk to NetrunnerDB
        self.data = CardData(None, None, None, None)
        self.data.load()

        # Initiate a refresh of the source data from NetrunnerDB
        self.refresh_data()

    def refresh_data(self):
        """Refreshes the card data from the Netrunner DB source"""
        try:
            refresh_begin = datetime.now()

            # We want to keep all of the ids, indexed by their card code so we can quickly access them
            ids = {}

            # We want to keep a mapping of the card name to it's card code to quickly look things up by name
            name_to_code = {}

            # We want to maintain the lists of corp and runner ids to show in drop downs
            # so that we don't need to regenerate them for every page
            # We also split them into legal and non-legal sets so that they can be separated
            # when shown on the UI
            legal_corp_ids = set()
            non_legal_corp_ids = set()
            legal_runner_ids = set()
            non_legal_runner_ids = set()

            # Go and fetch both the set of all cards, as well as the set of legal cards so we can collect all the info we need
            card_data = requests.get(
                "https://netrunnerdb.com/api/2.0/public/cards", timeout=5
            ).json()

            standard_legal_ids = requests.get(
                "https://api.netrunnerdb.com/api/v3/public/cards?filter%5Bsearch%5D=snapshot:standard_30%20t:runner_identity%7Ccorp_identity&fields%5Bcards%5D=title"
            )
            standard_legal_ids = [
                card["attributes"]["title"]
                for card in standard_legal_ids.json()["data"]
            ]

            # We only want to loop over these cards once at refresh time, and never again, so lets build all
            # the data structures we need for quick access in the future
            for card in card_data["data"]:
                card_code = int(card["code"])

                name = card["stripped_title"]
                name = name.replace("\u201c", '"')
                name = name.replace("\u201d", '"')

                if card["type_code"] == "identity":
                    # store whether this card is legal or not so we only need to search the list once
                    is_legal = name in standard_legal_ids
                    side = card["side_code"]

                    name_to_code[name] = card_code
                    ids[card_code] = {
                        "code": card_code,
                        "side": side,
                        "faction": card["faction_code"],
                        "name": name,
                        "legal": is_legal,
                    }

                    if is_legal:
                        if side == "corp":
                            legal_corp_ids.add(name)
                        else:
                            legal_runner_ids.add(name)
                    else:
                        if side == "corp":
                            non_legal_corp_ids.add(name)
                        else:
                            non_legal_runner_ids.add(name)

            # Sort the legal and non-legal runner ids for rendering in the UI
            legal_runner_ids = list(legal_runner_ids)
            legal_runner_ids.sort()
            legal_corp_ids = list(legal_corp_ids)
            legal_corp_ids.sort()
            non_legal_runner_ids = list(non_legal_runner_ids)
            non_legal_runner_ids.sort()
            non_legal_corp_ids = list(non_legal_corp_ids)
            non_legal_corp_ids.sort()
            runner_ids = (
                legal_runner_ids + [" --- Non Standard IDs --- "] + non_legal_runner_ids
            )
            corp_ids = (
                legal_corp_ids + [" --- Non Standard IDs --- "] + non_legal_corp_ids
            )

            # Store all data under 1 reference so we can swap the entire data set in one atomic update
            data = CardData(ids, name_to_code, runner_ids, corp_ids)

            # Write to disk for backup purposes
            data.save()

            refresh_duration = (datetime.now() - refresh_begin).microseconds / 1000
            logger.info(f"Refreshed card data in {refresh_duration}ms")

            # Construct the new data structures then swap the single reference at the end for thread safety
            self.data = data
        except Exception as e:
            logger.error(
                f"Failed to refresh card data. Retaining existing data. Error: {e}"
            )

    def get_faction(self, name: str):
        """Given the card name, return the faction it belongs to"""
        return self.data.get_faction(name)

    def corp_ids(self):
        return self.data.corp_ids

    def runner_ids(self):
        return self.data.runner_ids


# Export a reference to the data so that it's loaded only once and we can continue to use it
# without needing to reprocess the card data again
data = Cards()


def refresh_card_list():
    """In the background, every hour, refresh the card data"""
    while True:
        # We can sleep before refreshing the data, as the data is initialised
        # when we initially construct the CardData object
        sleep(60 * 60)
        data.refresh_data()


# When this module is first loaded, start a background task that will periodically
# refresh the card data in the background, as to not do it during a request from a user
Thread(target=refresh_card_list, daemon=True).start()
