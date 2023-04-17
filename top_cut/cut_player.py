from aesops import db
from sqlalchemy.orm import Mapped


class CutPlayer(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    player_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("player.id"))
    seed = db.Column(db.Integer)
    player = db.relationship("Player", backref="cut_player")
    cut_id = db.Column(
        db.Integer,
        db.ForeignKey("cut.id", ondelete="CASCADE", name="cut_id_fk"),
    )
    elim_round = db.Column(db.Integer)

    cut = db.relationship("Cut", backref="players")

    __table_args__ = (
        db.UniqueConstraint("cut_id", "seed", name="cut_player_seed_unique"),
    )

    def __repr__(self) -> str:
        return f"<CutPlayer> ID: {self.id} - {self.player}"

    def get_side_balance(self):
        corp_games = len([match for match in self.corp_cut_matches if match.concluded])
        runner_games = len(
            [match for match in self.runner_cut_matches if match.concluded]
        )
        return corp_games - runner_games
