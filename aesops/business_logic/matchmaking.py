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
    tournament: Tournament,
    corp_player: Player,
    runner_player: Player,
    is_bye=False,
    table_number=None,
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
    return m


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
    fixed_table_numbers = []
    graph = Graph()
    pairing_pool, bye_players = t_logic.bye_setup(t)
    shuffle(pairing_pool)
    for player in pairing_pool:
        graph.add_node(player.id)
        if player.fixed_table:
            fixed_table_numbers.append(player.table_number)
    for pair in combinations(pairing_pool, 2):
        pair_weight = find_min_edge(*pair)
        if pair_weight < 100:
            graph.add_edge(pair[0].id, pair[1].id, weight=1000 - pair_weight)
        else:
            continue
    pairings = max_weight_matching(graph, maxcardinality=True)
    for pair in pairings:
        corp, runner = assign_side(
            db.session.query(Player).get(pair[0]),
            db.session.query(Player).get(pair[1]),
        )
        table_number = None
        if corp.fixed_table or runner.fixed_table:
            table_number = (
                corp.table_number if corp.fixed_table else runner.table_number
            )
        create_match(
            tournament=t,
            corp_player=corp,
            runner_player=runner,
            table_number=table_number,
        )
    if bye_players is not None:
        for player in bye_players:
            player.recieved_bye = True
            create_match(
                tournament=t, corp_player=player, runner_player=None, is_bye=True
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

    i = 1
    for match in ranked_matches:
        if match.table_number:
            continue
        while i in fixed_table_numbers:
            i += 1
        match.table_number = i
        db.session.add(match)
        i += 1
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
    balance_post = max(abs(corp_bal + 1), abs(runner_bal - 1))
    return 8 ** abs(balance_post)


def score_cost(corp_player: Player, runner_player: Player):
    c_score = p_logic.get_record(corp_player)["score"]
    r_score = p_logic.get_record(runner_player)["score"]
    return abs((c_score - r_score + 1) * (c_score - r_score)) / 6


def calc_cost(corp_player: Player, runner_player: Player):
    return (
        side_cost(corp_player, runner_player)
        + score_cost(corp_player, runner_player)
        + (has_played(corp_player, runner_player) * 5)
        + bye_vs_bye_penalty(
            corp_player, runner_player, corp_player.tournament.current_round
        )
    )


def find_min_edge(p1: Player, p2: Player):
    options = legal_options(p1, p2)
    min_cost = 1000
    if options[0]:
        min_cost = min(calc_cost(p1, p2), min_cost)
    if options[1]:
        min_cost = min(calc_cost(p2, p1), min_cost)
    print(f"Min cost between {p1.name} and {p2.name}: {min_cost}")
    return min_cost


def has_played(p1: Player, p2: Player):
    if p2.id in [m.corp_player_id for m in p1.runner_matches]:
        return True
    if p2.id in [m.runner_player_id for m in p1.corp_matches]:
        return True
    return False


def bye_vs_bye_penalty(p1: Player, p2: Player, round: int):
    if not p1.first_round_bye or not p2.first_round_bye:
        return 0
    else:
        print(f"Both players received a bye by round {round}")
        return max(
            12 - round, 0
        )  # Penalize by 8 for each round they both received a bye, but not more than 8


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
