from typing import Sequence

import aesops.business_logic.match as m_logic
import aesops.business_logic.players as p_logic
from data_models.match import Match
from data_models.model_store import db
from data_models.players import Player
from random import shuffle

from data_models.model_store import Tournament

def add_player(
    tournament: Tournament, name, corp=None, runner=None, corp_deck=None, runner_deck=None
) -> Player:
    p = Player(
        name=name,
        corp=corp,
        runner=runner,
        corp_deck=corp_deck,
        runner_deck=runner_deck,
        tid=tournament.id,
    )
    db.session.add(p)
    db.session.commit()
    return p

def conclude_round(tournament: Tournament):
    for match in tournament.active_matches:
        m_logic.conclude(match)
    for player in tournament.players:
        p_logic.update_score(player)
        p_logic.update_sos_esos(player)
    db.session.add(tournament)
    db.session.commit()

def rank_players(tournament: Tournament) -> list[Player]:
    player_list = tournament.players
    if tournament.current_round == 0:
        player_list.sort(key=lambda x: x.name)
    else:
        player_list.sort(key=lambda x: x.esos, reverse=True)
        player_list.sort(key=lambda x: x.sos, reverse=True)
        player_list.sort(key=lambda x: p_logic.get_record(x)["score"], reverse=True)
    return player_list

def bye_setup(tournament: Tournament) -> tuple[list[Player], Player]:
    if len(tournament.active_players) % 2 == 0:
        return (tournament.active_players, None)
    player_list = rank_players(tournament).copy()
    if tournament.current_round > 1:
        elible_player_list = [
            p
            for p in player_list
            if not p.recieved_bye
            and p.active
            and (len(p.runner_matches) + len(p.corp_matches) > 0)
        ]
    else:
        elible_player_list = [p for p in player_list if not p.recieved_bye and p.active]
    if len(elible_player_list) == 0:
        elible_player_list = least_byes(tournament, player_list)
    elible_player_list.sort(key=lambda x: p_logic.get_record(x)["score"], reverse=True)
    bye_player = elible_player_list.pop(-1)
    pairable_players = tournament.active_players.copy()
    pairable_players.remove(bye_player)
    return (pairable_players, bye_player)

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
    return [p for p in tournament.active_players if not p_logic.is_paired(p, tournament.current_round)]

def is_current_round_finished(tournament: Tournament):
    return all([m.concluded for m in tournament.active_matches])
