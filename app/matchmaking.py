from random import random
from app import db
from app.models import Match, Player, Tournament
from networkx import Graph, max_weight_matching
from itertools import combinations

# TODO: Unpair round


class PairingException(Exception):
    pass


def create_match(tournament: Tournament, corp_player: Player, runner_player: Player):
    m = Match(
        tid=tournament.id,
        corp_player_id=corp_player.id,
        runner_player_id=runner_player.id,
        rnd=tournament.current_round,
    )
    db.session.add(m)
    db.session.commit()


def pair_round(t: Tournament):
    if all([m.concluded for m in t.active_matches]):
        raise PairingException("Not all active matches are finished")
    t.current_round += 1
    db.session.add(t)
    db.session.commit()
    graph = Graph()
    t.bye_setup()
    for player in t.active_players:
        graph.add_node(player.id)
    for pair in combinations(t.active_players, 2):
        pair_weight = find_min_edge(*pair)
        graph.add_edge(pair[0].id, pair[1].id, weight=1000 - pair_weight)
    pairings = max_weight_matching(graph, maxcardinality=True)
    for pair in pairings:
        assign_side(
            db.session.query(Player).get(pair[0]),
            db.session.query(Player).get(pair[1]),
        )


def legal_options(p1: Player, p2: Player) -> list[bool]:
    p1_can_corp = True
    p2_can_corp = True
    if p2.id in [m.corp_player_id for m in p1.runner_matches]:
        p2_can_corp = False
    if p2.id in [m.runner_player_id for m in p1.corp_matches]:
        p1_can_corp = False
    return [p1_can_corp, p2_can_corp]


def side_cost(corp_player: Player, runner_player: Player):
    balance_post = abs(corp_player.get_side_balance() + 1) + abs(
        runner_player.get_side_balance() - 1
    )
    balance_pre = abs(corp_player.get_side_balance()) + abs(
        runner_player.get_side_balance()
    )
    if balance_post > balance_pre and balance_pre != 0:
        return 1000
    return 8 ** abs(balance_post)


def score_cost(corp_player: Player, runner_player: Player):
    c_score = corp_player.get_record()["score"]
    r_score = runner_player.get_record()["score"]
    return (c_score - r_score + 1) * (c_score - r_score) / 6


def calc_cost(corp_player: Player, runner_player: Player):
    return side_cost(corp_player, runner_player) + score_cost(
        corp_player, runner_player
    )


def find_min_edge(p1: Player, p2: Player):
    options = legal_options(p1, p2)
    min_cost = 1000
    if options[0]:
        min_cost = min(calc_cost(p1, p2), min_cost)
    if options[1]:
        min_cost = min(calc_cost(p2, p1), min_cost)
    return min_cost


def assign_side(p1: Player, p2: Player):
    if p1.get_side_balance() > p2.get_side_balance():
        corp = p2
        runner = p1
    elif p2.get_side_balance() > p1.get_side_balance():
        corp = p1
        runner = p2
    elif random() > 0.5:
        corp = p1
        runner = p2
    else:
        corp = p2
        runner = p1
    create_match(tournament=p1.tournament, corp_player=corp, runner_player=runner)
