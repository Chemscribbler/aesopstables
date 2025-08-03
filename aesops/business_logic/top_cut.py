from data_models.model_store import db
from data_models.top_cut import Cut, CutPlayer, ElimMatch
from sqlalchemy import and_
from data_models.exceptions import ConclusionError
from data_models.players import Player
from data_models.tournaments import Tournament
import aesops.business_logic.elim_match as e_logic
import aesops.business_logic.tournament as t_logic
from random import randint
from .cut_tables import get_bracket


def get_side_balance(cut_player: CutPlayer):
    corp_games = len(
        [match for match in cut_player.corp_cut_matches if match.concluded]
    )
    runner_games = len(
        [match for match in cut_player.runner_cut_matches if match.concluded]
    )
    return corp_games - runner_games


def get_players_by_seed(cut: Cut):
    player_list = cut.players
    player_list.sort(key=lambda x: x.seed)
    return player_list


def generate_round(cut: Cut):
    bracket = get_bracket(cut.num_players, cut.double_elim)
    print(f"Bracket: {bracket}")
    for match in cut.matches:
        if not match.concluded:
            raise ConclusionError(
                "All matches must be concluded before generating next round"
            )
    if cut.rnd == 1:
        plyrs = get_players_by_seed(cut)
        for m in bracket["round_1"]:
            match = ElimMatch(cut_id=cut.id, rnd=1, table_number=m["table"])
            e_logic.add_player(match, plyrs[m["higher_seed"] - 1])
            e_logic.add_player(match, plyrs[m["lower_seed"] - 1])
            e_logic.determine_sides(match)
            db.session.add(match)
        db.session.commit()
    else:
        if get_standings(cut)["unranked_players"] == 0:
            raise ValueError("All Players have been ranked")
        matches = bracket[f"round_{cut.rnd}"]
        for match in matches:
            cut_match = ElimMatch(
                cut_id=cut.id, rnd=cut.rnd, table_number=match["table"]
            )
            if cut.num_players == 3:
                plyrs = get_players_by_seed(cut)
                player = plyrs[0]
            else:
                table_number, who_grab = match["higher_seed"]
                if who_grab == "winner":
                    print(f"Getting table {table_number} winner")
                    player = e_logic.get_winner(get_match_by_table(cut, table_number))
                elif who_grab == "loser":
                    print(f"Getting table {table_number} loser")
                    player = e_logic.get_loser(get_match_by_table(cut, table_number))
                else:
                    raise ValueError(f"Invalid value for who_grab: {who_grab}")
            print(player)
            e_logic.add_player(cut_match, player)
            print(cut_match.higher_seed)
            table_number, who_grab = match["lower_seed"]
            if who_grab == "winner":
                print(f"Getting table {table_number} winner")
                player = e_logic.get_winner(get_match_by_table(cut, table_number))
            elif who_grab == "loser":
                print(f"Getting table {table_number} loser")
                player = e_logic.get_loser(get_match_by_table(cut, table_number))
            e_logic.add_player(cut_match, player)
            print(cut_match.higher_seed)
            print(cut_match.lower_seed)
            e_logic.determine_sides(cut_match, is_second_final=is_second_final(cut))
            db.session.add(cut_match)
        db.session.commit()


def get_match_by_table(cut: Cut, table_number):
    match = ElimMatch.query.filter(
        and_(ElimMatch.table_number == table_number, ElimMatch.cut_id == cut.id)
    ).first()
    return match


def create(cut: Cut, tournament: Tournament, num_players: int, double_elim: bool):
    cut.tid = tournament.id
    if num_players not in [3, 4, 8, 16]:
        raise ValueError(f"Invalid number of players for cut {num_players}")
    cut.num_players = num_players
    cut.double_elim = double_elim
    db.session.add(cut)
    db.session.commit()
    top_players = t_logic.top_n_cut(tournament, n=num_players)
    for i, player in enumerate(top_players):
        cut_player = CutPlayer()
        cut_player.player_id = player["id"]
        cut_player.seed = i + 1
        cut_player.cut_id = cut.id
        db.session.add(cut_player)
    db.session.commit()


def destroy(cut: Cut):
    for match in ElimMatch.query.filter_by(cut_id=cut.id).all():
        db.session.delete(match)

    for player in CutPlayer.query.filter_by(cut_id=cut.id).all():
        db.session.delete(player)
    db.session.delete(cut)
    db.session.commit()


def conclude_round(cut: Cut):
    for match in cut.current_matches:
        e_logic.conclude(match)
    cut.rnd += 1
    db.session.add(cut)
    db.session.commit()


def get_standings(cut: Cut):
    players = cut.players
    # Check to see if only one player hasn't been eliminated
    # Check length of players with no value for elim_round
    if len([player for player in players if player.elim_round is None]) == 0:
        players.sort(key=lambda x: x.seed)
        players.sort(key=lambda x: x.elim_round, reverse=True)
        return {"ranked_players": players, "unranked_players": 0}
    else:
        eliminated_players = [player for player in players if player.elim_round]
        eliminated_players.sort(key=lambda x: x.seed)
        eliminated_players.sort(key=lambda x: x.elim_round, reverse=True)
        remaining_players = [player for player in players if not player.elim_round]
        return {
            "ranked_players": eliminated_players,
            "unranked_players": len(remaining_players),
        }


def get_round(cut: Cut, rnd: int):
    return ElimMatch.query.filter(
        and_(ElimMatch.cut_id == cut.id, ElimMatch.rnd == rnd)
    ).all()


def delete_round(cut: Cut, rnd: int):
    if rnd == 1:
        raise ValueError("Cannot delete first round")
    if rnd < cut.rnd:
        raise ValueError("Cannot delete round that has already been played")
    if rnd > cut.rnd:
        raise ValueError("Cannot delete future round")
    for match in get_round(cut, rnd):
        db.session.delete(match)
        db.session.commit()
    cut.rnd -= 1
    db.session.add(cut)
    db.session.commit()
    for player in cut.players:
        if player.elim_round is None:
            continue
        if player.elim_round >= rnd:
            player.elim_round = None
            db.session.add(player)
            db.session.commit()


def is_second_final(cut: Cut):
    if not cut.double_elim:
        return False
    bracket = get_bracket(cut.num_players, cut.double_elim)
    round_numbers = [int(round_name.split("_")[1]) for round_name in bracket.keys()]
    return cut.rnd == max(round_numbers)
