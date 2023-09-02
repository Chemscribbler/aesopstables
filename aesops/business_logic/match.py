from data_models.exceptions import ConclusionError
from data_models.match import Match
from data_models.model_store import db
from . import players as p_logic

def conclude(match :Match):
    if match.result not in [-1, 0, 1]:
        raise ConclusionError("No result recorded")
    match.concluded = True
    db.session.add(match)
    db.session.commit()

def corp_win(match :Match):
    match.result = 1
    db.session.add(match)
    db.session.commit()

def runner_win(match :Match):
    match.result = -1
    db.session.add(match)
    db.session.commit()

def tie(match :Match):
    match.result = 0
    db.session.add(match)
    db.session.commit()

def reset(match :Match):
    match.result = None
    match.concluded = False
    db.session.add(match)
    db.session.commit()

def delete(match :Match):
    if match.is_bye:
        match.corp_player.recieved_bye = False
        p_logic.reset(match.corp_player)
    else:
        p_logic.corp_player.reset(match.corp_player)
        p_logic.runner_player.reset(match.runner_player)
    db.session.delete(match)
    db.session.commit()
