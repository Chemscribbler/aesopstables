from aesops import db
from pairing.player import Player
from pairing.match import Match
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
        match.conclude()
    for player in tournament.players:
        player.update_score()
        player.update_sos_esos()
    db.session.add(tournament)
    db.session.commit()

def rank_players(tournament: Tournament) -> list[Player]:
    player_list = tournament.players
    player_list.sort(key=lambda x: x.esos, reverse=True)
    player_list.sort(key=lambda x: x.sos, reverse=True)
    player_list.sort(key=lambda x: x.get_record()["score"], reverse=True)
    return player_list

def bye_setup(tournament: Tournament) -> tuple[list[Player], Player]:
    if len(tournament.active_players) % 2 == 0:
        return (tournament.active_players, None)
    player_list = rank_players(tournament).copy()
    elible_player_list = [p for p in player_list if not p.recieved_bye and p.active]
    if len(elible_player_list) == 0:
        raise Exception("No elible players for a bye")
    elible_player_list.sort(key=lambda x: x.get_record()["score"], reverse=True)
    bye_player = elible_player_list.pop(-1)
    pairable_players = tournament.active_players.copy()
    pairable_players.remove(bye_player)
    return (pairable_players, bye_player)

def get_round(tournament: Tournament, round) -> list[Match]:
    return [m for m in tournament.matches if m.rnd == round]

def unpair_round(tournament: Tournament):
    if tournament.cut is not None:
        raise Exception("Cannot unpair a round after a cut has been made")
    for match in tournament.active_matches:
        match.delete()
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
    return [p for p in tournament.active_players if not p.is_paired(tournament.current_round)]

def is_current_round_finished(tournament: Tournament):
    return all([m.concluded for m in tournament.active_matches])
