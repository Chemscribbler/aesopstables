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


class CachedPlayer:
    def __init__(self, player: Player):
        self.id = player.id
        self.score = player.score
        self.side_bias = p_logic.get_side_balance(player)
        self.active = player.active
        self.corp_matches = p_logic.get_opponent_ids(player, side="corp")
        self.runner_matches = p_logic.get_opponent_ids(player, side="runner")
        self.fixed_table = player.fixed_table

    def __repr__(self):
        return f"<CachedPlayer {self.name} ({self.id})>"


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
    pairing_pool_dict = {player.id: CachedPlayer(player) for player in pairing_pool}
    for pid, player in pairing_pool_dict.items():
        graph.add_node(pid)
        if player.fixed_table:
            fixed_table_numbers.append(player.table_number)
    for pair in combinations(pairing_pool_dict, 2):
        pair_weight = find_min_edge(
            pairing_pool_dict[pair[0]], pairing_pool_dict[pair[1]]
        )
        if pair_weight < 100:
            graph.add_edge(pair[0], pair[1], weight=1000 - pair_weight)
        else:
            continue
    pairings = max_weight_matching(graph, maxcardinality=True)
    for pair in pairings:
        corp, runner = assign_side(
            pairing_pool_dict[pair[0]], pairing_pool_dict[pair[1]]
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
            db.session.add(player)
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


def legal_options(p1: CachedPlayer, p2: CachedPlayer) -> list[bool]:
    p1_can_corp = True
    p2_can_corp = True
    if p2.id in p1.runner_matches:
        p2_can_corp = False
    if p2.id in p1.corp_matches:
        p1_can_corp = False
    return [p1_can_corp, p2_can_corp]


def side_cost(corp_player: CachedPlayer, runner_player: CachedPlayer):
    balance_factor = max(
        abs(max(corp_player.side_bias, 0)), abs(min(runner_player.side_bias, 0))
    )
    return 50 ** abs(balance_factor)


def score_cost(corp_player: CachedPlayer, runner_player: CachedPlayer):
    return (corp_player.score - runner_player.score) ** 2


def calc_cost(corp_player: CachedPlayer, runner_player: CachedPlayer):
    return (
        side_cost(corp_player, runner_player)
        + score_cost(corp_player, runner_player)
        + (has_played(corp_player, runner_player) * 5)
        # + bye_vs_bye_penalty(
        #     corp_player, runner_player, corp_player.tournament.current_round
        # )
    )


def find_min_edge(p1: CachedPlayer, p2: CachedPlayer):
    options = legal_options(p1, p2)
    min_cost = 1000
    if options[0]:
        min_cost = min(calc_cost(p1, p2), min_cost)
    if options[1]:
        min_cost = min(calc_cost(p2, p1), min_cost)
    # print(f"Min cost between {p1.name} and {p2.name}: {min_cost}")
    return min_cost


def has_played(p1: CachedPlayer, p2: CachedPlayer):
    if p2.id in p1.corp_matches:
        return True
    if p2.id in p1.runner_matches:
        return True
    return False


def assign_side(p1: CachedPlayer, p2: CachedPlayer) -> tuple[Player, Player]:

    # Currently this sorta breaks if it's the third times players are matched
    if p1.id in p2.runner_matches:
        corp = p2
        runner = p1
    elif p2.id in p1.runner_matches:
        corp = p1
        runner = p2
    elif p1.side_bias > p2.side_bias:
        corp = p2
        runner = p1
    elif p2.side_bias > p1.side_bias:
        corp = p1
        runner = p2
    elif random() > 0.5:
        corp = p1
        runner = p2
    else:
        corp = p2
        runner = p1
    return (db.session.get(Player, corp.id), db.session.get(Player, runner.id))
