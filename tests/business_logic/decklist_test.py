from aesops.business_logic.decklist import decklist_parser

"""
Ensuring that the deck with Knickknack included parses without throwing
an exception
"""
def test_parse_knickknack_deck():
    with open("test_data/knickknack_deck.txt") as f:
        decklist = decklist_parser(f.read().rstrip())
