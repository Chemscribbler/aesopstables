from pairing.tournament import Tournament
from pairing.player import Player
from aesops import db


class CutMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("tournament.id"))
    tournament = db.relationship("Tournament", back_populates="cut_matches")
    rnd = db.Column(db.Integer)
    corp_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    runner_player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    corp_player = db.relationship(
        "Player", foreign_keys=[corp_player_id], back_populates="cut_matches"
    )
    runner_player = db.relationship(
        "Player", foreign_keys=[runner_player_id], back_populates="cut_matches"
    )
    result = db.Column(db.Integer)
    concluded = db.Column(db.Boolean, default=False)

    def __repr__(self) -> str:
        return f"<CutMatch> {self.tournament.name}: {self.id}"
