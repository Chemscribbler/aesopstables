from random import choices, random
from string import ascii_uppercase
from data_models.tournaments import Tournament
import aesops.business_logic.tournament as t_logic
from pairing.match import Match
from pairing.matchmaking import pair_round
from data_models.model_store import db
import tqdm


def create_players(t: Tournament, count: int):
    for _ in range(count):
        t_logic.add_player(t, "".join(choices(ascii_uppercase, k=5)))


def sim_round(t: Tournament):
    for m in t.active_matches:
        if m.concluded:
            continue
        r = random()
        if r < 0.49:
            m.corp_win()
        elif r < 0.51:
            m.tie()
        else:
            m.runner_win()

    t_logic.conclude_round(t)


def display_players(t: Tournament):
    for p in t_logic.rank_players(t):
        print(f"{p.name} {p.score} {p.sos} {p.esos}")


def sim_tournament(n_players: int, n_rounds: int, name: str = None):
    if name is None:
        t = Tournament()
    else:
        t = Tournament(name=name)
    db.session.add(t)
    db.session.commit()
    create_players(t, count=n_players)
    for _ in range(n_rounds):
        pair_round(t)
        sim_round(t)
    return t


def run_sims(n_tournaments: int, prefix: str = "Sim_", **kwargs):
    t_list = []
    for i in tqdm.trange(n_tournaments):
        t_list.append(sim_tournament(name=prefix + str(i), **kwargs))

    for t in t_list:
        print(get_report(t))


def get_report(t: Tournament, cutoff: int = 1):
    players = t_logic.rank_players(t)
    max_score = 0
    num_max = 0
    cutoff_score = 0
    num_bubbled = 0
    num_mismatched = 0
    for i, player in enumerate(players):
        if player.score > max_score:
            max_score = player.score
            num_max = 1
        elif player.score == max_score:
            num_max += 1
        if len(player.corp_matches) != len(player.runner_matches):
            num_mismatched += 1

        if i == cutoff - 1:
            cutoff_score = player.score
            continue
        if player.score == cutoff_score:
            num_bubbled += 1

    return {
        "id": t.id,
        "max_score": max_score,
        "num_bubbled": num_bubbled,
        "num_uneven": num_mismatched,
    }
