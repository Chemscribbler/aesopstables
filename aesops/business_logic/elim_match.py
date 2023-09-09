from data_models.exceptions import ConclusionError
from data_models.match import MatchResult
from data_models.model_store import db
from data_models.top_cut import CutPlayer, ElimMatch
import aesops.business_logic.top_cut as tc_logic
from random import randint
from .cut_tables import get_bracket


def conclude(elim_match :ElimMatch):
    if elim_match.result not in [MatchResult.CORP_WIN.value, MatchResult.RUNNER_WIN.value]:
        raise ConclusionError("No result recorded")
    elim_match.concluded = True
    if elim_match.result == MatchResult.CORP_WIN.value:
        elim_match.winner_id = elim_match.corp_player_id
        elim_match.loser_id = elim_match.runner_player_id
    else:
        elim_match.winner_id = elim_match.runner_player_id
        elim_match.loser_id = elim_match.corp_player_id
    update_elim(elim_match)
    db.session.add(elim_match)
    db.session.commit()

def corp_win(elim_match :ElimMatch):
    elim_match.result = MatchResult.CORP_WIN.value
    db.session.add(elim_match)
    db.session.commit()

def runner_win(elim_match :ElimMatch):
    elim_match.result = MatchResult.RUNNER_WIN.value
    db.session.add(elim_match)
    db.session.commit()

def reset(elim_match :ElimMatch):
    elim_match.result = None
    elim_match.concluded = False
    db.session.add(elim_match)
    db.session.commit()

def add_player(elim_match :ElimMatch, cutplayer: CutPlayer):
    """_summary_: Adds a player to the match."""
    if elim_match.higher_seed_id is None:
        elim_match.higher_seed_id = cutplayer.id
    elif elim_match.lower_seed_id is None:
        # Because lower numbered seed is higher seed
        if cutplayer.seed < CutPlayer.query.get(elim_match.higher_seed_id).seed:
            elim_match.lower_seed_id = elim_match.higher_seed_id
            elim_match.higher_seed_id = cutplayer.id
        else:
            elim_match.lower_seed_id = cutplayer.id
    else:
        raise Exception("Match is full")
    db.session.add(elim_match)
    db.session.commit()

def determine_sides(elim_match :ElimMatch, is_second_final=False):
    """_summary_: Determines the sides of the match based on the side balance of the players.
    If the side balance is equal, it will randomly choose a side for each player.
    Otherwise, the player with the higher side balance will be the runner player.
    """
    if is_second_final:
        prior_match = tc_logic.get_match_by_table(elim_match.cut, elim_match.table_number - 1)
        elim_match.corp_player_id = prior_match.runner_player_id
        elim_match.runner_player_id = prior_match.corp_player_id
        db.session.add(elim_match)
        db.session.commit()
        return elim_match
    higher_seed = CutPlayer.query.get(elim_match.higher_seed_id)
    lower_seed = CutPlayer.query.get(elim_match.lower_seed_id)
    if tc_logic.get_side_balance(higher_seed) > tc_logic.get_side_balance(lower_seed):
        elim_match.corp_player_id = elim_match.lower_seed_id
        elim_match.runner_player_id = elim_match.higher_seed_id
    elif tc_logic.get_side_balance(higher_seed) < tc_logic.get_side_balance(lower_seed):
        elim_match.corp_player_id = elim_match.higher_seed_id
        elim_match.runner_player_id = elim_match.lower_seed_id
    else:
        if randint(0, 1):
            elim_match.corp_player_id = elim_match.lower_seed_id
            elim_match.runner_player_id = elim_match.higher_seed_id
        else:
            elim_match.corp_player_id = elim_match.higher_seed_id
            elim_match.runner_player_id = elim_match.lower_seed_id
    db.session.add(elim_match)
    db.session.commit()
    return elim_match

def get_winner(elim_match :ElimMatch):
    """_summary_: Returns the winner of the match."""
    if elim_match.result == MatchResult.CORP_WIN.value:
        return elim_match.corp_player
    elif elim_match.result == MatchResult.RUNNER_WIN.value:
        return elim_match.runner_player
    else:
        raise ConclusionError("Match has not been concluded")

def get_loser(elim_match :ElimMatch):
    """_summary_: Returns the loser of the match."""
    if elim_match.result == MatchResult.CORP_WIN.value:
        return elim_match.runner_player
    elif elim_match.result == MatchResult.RUNNER_WIN.value:
        return elim_match.corp_player
    else:
        raise ConclusionError("Match has not been concluded")

def update_elim(elim_match :ElimMatch):
    """
    Checks against the bracket and updates the loser's elimination round if relevant.
    """
    bracket = get_bracket(elim_match.cut.num_players, elim_match.cut.double_elim)
    for match in bracket[f"round_{elim_match.rnd}"]:
        if match["table"] == elim_match.table_number:
            if "final" in match.keys() and not match["elim"]:

                lower_semis_table_number = elim_match.table_number - 1
                semi_winner_id = (
                    get_winner(tc_logic.get_match_by_table(elim_match.cut, lower_semis_table_number)).id
                )
                print(semi_winner_id)
                print(elim_match.loser_id)
                if semi_winner_id == elim_match.loser_id:
                    print("Second Final Not Needed")
                    get_loser(elim_match).elim_round = elim_match.rnd
                    get_winner(elim_match).elim_round = elim_match.rnd + 1
                    db.session.add(get_loser(elim_match))
                    db.session.add(get_winner(elim_match))
                    db.session.commit()
            else:
                if match["elim"]:
                    get_loser(elim_match).elim_round = elim_match.rnd
                    db.session.add(get_loser(elim_match))
                    db.session.commit()
                    if "final" in match.keys():

                        get_winner(elim_match).elim_round = elim_match.rnd + 1
                        db.session.add(get_winner(elim_match))
                        db.session.commit()

def swap_sides(elim_match :ElimMatch):
    """_summary_: Swaps the sides of the match."""
    elim_match.corp_player_id, elim_match.runner_player_id = (
        elim_match.runner_player_id,
        elim_match.corp_player_id,
    )
    db.session.add(elim_match)
    db.session.commit()
