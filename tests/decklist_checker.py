from aesops.utility import decklist_parser


def import_decklist_from_file(filepath: str):
    decklist = None
    with open(filepath, "r", encoding="utf-8") as f:
        decklist = decklist_parser(f.read())
    return decklist
