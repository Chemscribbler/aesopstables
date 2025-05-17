from data_models.model_store import db
from sqlalchemy import Enum

import enum


def convert_result_to_score(result, side):
    if side not in ["corp", "runner"]:
        raise ValueError("Side must be either 'corp' or 'runner'")
    if result == MatchResult.CORP_WIN.value:
        return 3 if side == "corp" else 0
    elif result == MatchResult.RUNNER_WIN.value:
        return 0 if side == "corp" else 3
    elif result == MatchResult.DRAW.value:
        return 1
    elif result == MatchResult.INTENTIONAL_DRAW.value:
        return 1
    else:
        raise ValueError("Invalid match result")


class MatchResult(enum.Enum):
    CORP_WIN = 1
    RUNNER_WIN = -1
    DRAW = 0
    INTENTIONAL_DRAW = 9


class MatchReport(enum.Enum):
    CORP_WIN = 1
    RUNNER_WIN = 2
    DRAW = 0
    INTENTIONAL_DRAW = 9


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    rnd = db.Column(db.Integer)
    corp_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)
    is_bye = db.Column(db.Boolean, default=False)
    table_number = db.Column(db.Integer)

    corp_player = db.relationship(
        "Player",
        foreign_keys=[corp_player_id],
        backref="corp_matches",
    )
    runner_player = db.relationship(
        "Player", foreign_keys=[runner_player_id], backref="runner_matches"
    )
    tournament = db.relationship("Tournament", back_populates="matches")

    def __repr__(self) -> str:
        return f"<Match> TID: {self.tid} - RND: {self.rnd} - Result: {self.result}"
