from typing import Sequence

import aesops.business_logic.match as m_logic
import aesops.business_logic.players as p_logic
from data_models.match import Match, MatchResult
from data_models.model_store import db, Tournament
from data_models.players import Player
from random import shuffle


def add_player(
    tournament: Tournament,
    name,
    corp=None,
    runner=None,
    corp_deck=None,
    runner_deck=None,
    user_id=None,
    first_round_bye=False,
) -> Player:
    p = Player(
        name=name,
        corp=corp,
        runner=runner,
        corp_deck=corp_deck,
        runner_deck=runner_deck,
        tid=tournament.id,
        uid=None if user_id is None else user_id,
        first_round_bye=first_round_bye,
    )
    db.session.add(p)
    db.session.commit()
    return p


# TODO: Can this be safely cached?
def get_record_from_memory(player: Player, matches: dict, count_byes=True):
    score = 0
    games_played = 0
    for match in player.runner_matches:
        mem_match = matches[match.id]
        if mem_match.result == MatchResult.RUNNER_WIN.value and mem_match.concluded:
            score += 3
        if (
            mem_match.result
            in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value]
            and mem_match.concluded
        ):
            score += 1
        games_played += 1
    for match in player.corp_matches:
        mem_match = matches[match.id]
        if mem_match.result == MatchResult.CORP_WIN.value and mem_match.concluded:
            score += 3
        if (
            mem_match.result
            in [MatchResult.DRAW.value, MatchResult.INTENTIONAL_DRAW.value]
            and mem_match.concluded
        ):
            score += 1
        if count_byes or not mem_match.is_bye:
            games_played += 1
    return {"score": score, "games_played": games_played}


def update_score_from_memory(player: Player, matches=dict):
    return get_record_from_memory(player, matches, count_byes=True)["score"]


def get_average_score_from_memory(player: Player, matches: dict):
    record = get_record_from_memory(player, matches, count_byes=False)
    return record["score"] / max(record["games_played"], 1)


def update_sos_from_memory(player: Player, matches: dict, players: dict):
    opp_average_score = sum(
        [
            get_average_score_from_memory(players[m.corp_player_id], matches=matches)
            for m in player.runner_matches
        ]
    )
    opp_average_score += sum(
        [
            get_average_score_from_memory(players[m.runner_player_id], matches=matches)
            for m in player.corp_matches
            if m.is_bye == False
        ]
    )
    return round(
        opp_average_score
        / max(
            get_record_from_memory(player, matches=matches, count_byes=False)[
                "games_played"
            ],
            1,
        ),
        3,
    )


def get_opponent(player: Player, match: Match, players: dict):
    if match.corp_player_id == player.id:
        return players[match.runner_player.id]
    return players[match.corp_player.id]


def update_esos_from_memory(player: Player, matches: dict, players: dict):
    opp_total_sos = sum(
        [
            get_opponent(player, match=m, players=players).sos
            for m in player.runner_matches
        ]
    )
    opp_total_sos += sum(
        [
            get_opponent(player, match=m, players=players).sos
            for m in player.corp_matches
            if m.is_bye == False
        ]
    )
    return round(
        opp_total_sos
        / max(
            get_record_from_memory(player, matches=matches, count_byes=False)[
                "games_played"
            ],
            1,
        ),
        3,
    )


def conclude_round(tournament: Tournament):
    for match in tournament.active_matches:
        m_logic.conclude(match)
    local_players = {p.id: p for p in tournament.players}
    matches = {m.id: m for m in tournament.matches}
    for player in local_players.values():
        player.score = update_score_from_memory(player, matches)
        db.session.add(player)
    db.session.commit()
    for player in tournament.players:
        player.sos = update_sos_from_memory(player, matches, local_players)
        db.session.add(player)
    db.session.commit()

    for player in tournament.players:
        player.esos = update_esos_from_memory(player, matches, local_players)
        db.session.add(player)
    db.session.commit()
    db.session.add(tournament)
    db.session.commit()
    return tournament


def calculate_player_ranks(tournament: Tournament):
    """
    Calculates the rankings for players in this tournament.

    Also gathers required information about the tournament results used to render
    the tournament page in a single pass of the results.
    """
    players = tournament.players

    # We're going to look at each match individually, but we need to keep
    # information about each player. So we keep this in a handy dictionary
    # for fast access
    player_map = {}
    for player in players:
        player_map[player.id] = {
            "player": player,
            "score": 0,
            "games_played": 0,
            "corp_record": {"W": 0, "L": 0, "T": 0},
            "runner_record": {"W": 0, "L": 0, "T": 0},
            "side_bias": 0,
            "active": player.active,
        }

    # To avoid multiple trips to the database per player, we iterate the
    # matches instead, updating the relevant player's results for each match
    for match in tournament.matches:
        # Select the player data for the current set of players
        corp_id = match.corp_player_id
        runner_id = match.runner_player_id
        corp_data = player_map[corp_id]
        if runner_id is not None:
            runner_data = player_map[runner_id]

        if match.concluded:
            # Players on a bye are set as the corp player
            # For the purposes of display we always count a bye as a game
            # but no change to the side bias
            if match.is_bye:
                corp_data["games_played"] += 1
                corp_data["score"] += 3
                continue

            # Each side played a game, so bump their counts
            corp_data["games_played"] += 1
            runner_data["games_played"] += 1

            # Adjust the bias score based upon which side they played
            corp_data["side_bias"] += 1
            runner_data["side_bias"] -= 1

            # Update each player's results based upon the result of the match
            if match.result == MatchResult.RUNNER_WIN.value:
                corp_data["corp_record"]["L"] += 1
                runner_data["runner_record"]["W"] += 1

                runner_data["score"] += 3

            elif match.result == MatchResult.CORP_WIN.value:
                corp_data["corp_record"]["W"] += 1
                runner_data["runner_record"]["L"] += 1

                corp_data["score"] += 3
            else:
                corp_data["corp_record"]["T"] += 1
                runner_data["runner_record"]["T"] += 1

                corp_data["score"] += 1
                runner_data["score"] += 1

    # This ranking matches what is done in the `rank_players` function below
    # However in the case of a tournament that has begun, we sort this list of players
    # 3 times which is not very efficient
    # A potential improvement here is to only sort the result once, and use a more complex function
    # to determine the final rank, but do it in a single pass (which is going to be much quicker
    # over larger tournaments)
    result = list(player_map.values())
    if tournament.current_round == 0:
        result.sort(key=lambda p: p["player"].name.lower())
    else:
        result.sort(
            key=lambda p: (p["score"], p["player"].sos, p["player"].esos), reverse=True
        )

    return result


def rank_players(tournament: Tournament) -> list[Player]:
    player_list = tournament.players
    if tournament.current_round == 0:
        player_list.sort(key=lambda x: x.name.lower())
    else:
        player_list.sort(key=lambda x: x.esos, reverse=True)
        player_list.sort(key=lambda x: x.sos, reverse=True)
        player_list.sort(key=lambda x: p_logic.get_record(x)["score"], reverse=True)
    return player_list


def first_round_byes(tournament: Tournament) -> tuple[list[Player], list[Player]]:
    guranteed_byes = [p for p in tournament.players if p.first_round_bye and p.active]
    non_bye_players = [
        p for p in tournament.players if not p.first_round_bye and p.active
    ]
    if len(non_bye_players) % 2 == 0:
        return (non_bye_players, guranteed_byes)
    else:
        shuffle(non_bye_players)
        bye_player = non_bye_players.pop(-1)
        guranteed_byes.append(bye_player)
        return (non_bye_players, guranteed_byes)


def bye_setup(tournament: Tournament) -> tuple[list[Player], Player]:
    if tournament.current_round == 1:
        return first_round_byes(tournament)
    if len(tournament.active_players) % 2 == 0:
        return (tournament.active_players, None)
    player_list = rank_players(tournament).copy()
    if tournament.current_round > 1:
        elible_player_list = [
            p
            for p in player_list
            if not p.received_bye
            and p.active
            and (
                p_logic.get_record(p, count_byes=False)["games_played"] > 0
            )  # This is to prevent late joiners from getting a bye their first round
        ]
    else:
        elible_player_list = [p for p in player_list if not p.received_bye and p.active]
        shuffle(elible_player_list)
    if len(elible_player_list) == 0:
        elible_player_list = least_byes(tournament, player_list)
    elible_player_list.sort(key=lambda x: p_logic.get_record(x)["score"], reverse=True)
    bye_player = elible_player_list.pop(-1)
    pairable_players = tournament.active_players.copy()
    pairable_players.remove(bye_player)
    return (pairable_players, [bye_player])


def least_byes(tournament: Tournament, all_players: Sequence[Player]) -> list[Player]:
    bye_count = {p: 0 for p in all_players if p.active}
    for match in tournament.matches:
        if not match.is_bye:
            continue
        player = match.corp_player
        if not player.active:
            continue
        bye_count[player] += 1
    min_num_byes = min(bye_count.values())
    return [player for player, count in bye_count.items() if count < min_num_byes + 1]


def get_round(tournament: Tournament, round) -> list[Match]:
    return [m for m in tournament.matches if m.rnd == round]


def unpair_round(tournament: Tournament):
    if tournament.cut is not None:
        raise Exception("Cannot unpair a round after a cut has been made")
    for match in tournament.active_matches:
        m_logic.delete(match)
    tournament.current_round -= 1
    db.session.add(tournament)
    db.session.commit()
    conclude_round(tournament)  # calling this to recalculate scores
    return tournament


def top_n_cut(tournament: Tournament, n):
    player_list = rank_players(tournament)
    cut_players = []
    for i in range(len(player_list)):
        if player_list[i].active:
            cut_players.append(player_list[i])
            if len(cut_players) == n:
                break
    # cut_players = player_list[:n]
    return cut_players


def get_unpaired_players(tournament: Tournament):
    return [
        p
        for p in tournament.active_players
        if not p_logic.is_paired(p, tournament.current_round)
    ]


def is_current_round_finished(tournament: Tournament):
    return all([m.concluded for m in tournament.active_matches])
