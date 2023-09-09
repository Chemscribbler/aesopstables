from data_models.exceptions import ConclusionError
from data_models.match import Match, MatchResult
from data_models.model_store import db
from . import players as p_logic

def conclude(match :Match):
    if match.result not in [MatchResult.CORP_WIN.Value, MatchResult.RUNNER_WIN.Value, MatchResult.DRAW.Value, MatchResult.INTENTIONAL_DRAW.Value]:
        raise ConclusionError("No result recorded")
    match.concluded = True
    db.session.add(match)
    db.session.commit()

def corp_win(match :Match):
    match.result = MatchResult.CORP_WIN.value
    db.session.add(match)
    db.session.commit()

def runner_win(match :Match):
    match.result = MatchResult.RUNNER_WIN.value
    db.session.add(match)
    db.session.commit()

def tie(match :Match):
    match.result = MatchResult.DRAW.value
    db.session.add(match)
    db.session.commit()

def intentional_draw(match :Match):
    match.result = MatchResult.INTENTIONAL_DRAW.value
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
        p_logic.reset(match.corp_player)
        p_logic.reset(match.runner_player)
    db.session.delete(match)
    db.session.commit()
