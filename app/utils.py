from random import choices, random
from string import ascii_uppercase
from app.models import Tournament


def create_players(t: Tournament, count: int):
    for _ in range(count):
        t.add_player("".join(choices(ascii_uppercase, k=5)))


def conclude_round(t: Tournament):
    r = random()
    for m in t.active_matches:
        if r < 0.45:
            m.corp_win()
        elif r < 0.55:
            m.tie()
        else:
            m.runner_win()

    t.conclude_round()
