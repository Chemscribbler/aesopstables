from aesops import db
from sqlalchemy.orm import Mapped


class CutPlayer(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    seed = db.Column(db.Integer)
    player = db.relationship("Player", backref="cut_player")
    cut_id = db.Column(db.Integer, db.ForeignKey("cut.id"))

    cut = db.relationship("Cut", backref="players")

    __table_args__ = (db.UniqueConstraint("cut_id", "seed"),)

    def __repr__(self) -> str:
        return f"<CutPlayer> ID: {self.id} - {self.player}"

    def get_side_balance(self):
        corp_games = len([match for match in self.corp_cut_matches if match.concluded])
        runner_games = len(
            [match for match in self.runner_cut_matches if match.concluded]
        )
        return corp_games - runner_games
