from random import random, shuffle
from data_models.exceptions import PairingException
from data_models.match import Match
from data_models.model_store import db
from data_models.players import Player
from data_models.tournaments import Tournament
import aesops.business_logic.players as p_logic
import aesops.business_logic.tournament as t_logic
from networkx import Graph, max_weight_matching
from itertools import combinations


def create_match(
    tournament: Tournament, corp_player: Player, runner_player: Player, is_bye=False, table_number=None
):
    if is_bye:
        m = Match(
            tid=tournament.id,
            corp_player_id=corp_player.id,
            rnd=tournament.current_round,
            is_bye=is_bye,
            result=1,
        )
    else:
        m = Match(
            tid=tournament.id,
            corp_player_id=corp_player.id,
            runner_player_id=runner_player.id,
            rnd=tournament.current_round,
            is_bye=is_bye,
        )
    if table_number:
        m.table_number = table_number
    db.session.add(m)
    db.session.commit()


def pair_round(t: Tournament):
    if not all([m.concluded for m in t.active_matches]):
        raise PairingException(
            f"Not all active matches are finished in current round: {t.current_round}"
        )
    if t.cut is not None:
        raise PairingException("Tournament is in cut - cannot pair swiss rounds")
    t.current_round += 1
    db.session.add(t)
    db.session.commit()
    graph = Graph()
    pairing_pool, bye_player = t_logic.bye_setup(t)
    shuffle(pairing_pool)
    for player in pairing_pool:
        graph.add_node(player.id)
    for pair in combinations(pairing_pool, 2):
        pair_weight = find_min_edge(*pair)
        graph.add_edge(pair[0].id, pair[1].id, weight=1000 - pair_weight)
    pairings = max_weight_matching(graph, maxcardinality=True)
    for pair in pairings:
        corp, runner = assign_side(
            db.session.query(Player).get(pair[0]),
            db.session.query(Player).get(pair[1]),
        )
        create_match(tournament=t, corp_player=corp, runner_player=runner)
    if bye_player is not None:
        bye_player.recieved_bye = True
        create_match(
            tournament=t, corp_player=bye_player, runner_player=None, is_bye=True
        )
    ranked_matches = sorted(
        t.active_matches,
        key=lambda m: (
            (
                p_logic.get_record(m.corp_player)["score"]
                + p_logic.get_record(m.runner_player)["score"]
            )
            if not m.is_bye
            else -1
        ),
        reverse=True,
    )
    for i, match in enumerate(ranked_matches):
        match.table_number = i + 1
        db.session.add(match)
    db.session.commit()


def legal_options(p1: Player, p2: Player) -> list[bool]:
    p1_can_corp = True
    p2_can_corp = True
    if p2.id in [m.corp_player_id for m in p1.runner_matches]:
        p2_can_corp = False
    if p2.id in [m.runner_player_id for m in p1.corp_matches]:
        p1_can_corp = False
    return [p1_can_corp, p2_can_corp]


def side_cost(corp_player: Player, runner_player: Player):
    corp_bal = p_logic.get_side_balance(corp_player)
    runner_bal = p_logic.get_side_balance(runner_player)
    balance_post = abs(corp_bal + 1) + abs(runner_bal - 1)
    balance_pre = abs(corp_bal) + abs(runner_bal)
    if balance_post > balance_pre and balance_pre != 0:
        return 1000
    return 8 ** abs(balance_post)


def score_cost(corp_player: Player, runner_player: Player):
    c_score = p_logic.get_record(corp_player)["score"]
    r_score = p_logic.get_record(runner_player)["score"]
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
    # Currently this sorta breaks if it's the third times players are matched
    if p1.id in [m.corp_player_id for m in p2.runner_matches]:
        corp = p2
        runner = p1
    elif p2.id in [m.corp_player_id for m in p1.runner_matches]:
        corp = p1
        runner = p2
    elif p_logic.get_side_balance(p1) > p_logic.get_side_balance(p2):
        corp = p2
        runner = p1
    elif p_logic.get_side_balance(p2) > p_logic.get_side_balance(p1):
        corp = p1
        runner = p2
    elif random() > 0.5:
        corp = p1
        runner = p2
    else:
        corp = p2
        runner = p1
    return (corp, runner)
