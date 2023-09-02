from data_models.model_store import db
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

class ElimMatch(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    cut_id = db.Column(
        db.Integer,
        db.ForeignKey("cut.id", ondelete="CASCADE", name="cut_id_fk"),
    )
    rnd: Mapped[int] = db.Column(db.Integer)
    higher_seed_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    lower_seed_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    corp_player_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    runner_player_id: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("cut_player.id")
    )
    result: Mapped[int] = db.Column(db.Integer)
    concluded: Mapped[bool] = db.Column(db.Boolean, default=False)
    winner_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    loser_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("cut_player.id"))
    table_number: Mapped[int] = db.Column(db.Integer)
    cut = db.relationship("Cut", backref="matches")
    higher_seed: Mapped[CutPlayer] = db.relationship(
        "CutPlayer", foreign_keys=[higher_seed_id], backref="higher_seed_matches"
    )
    lower_seed: Mapped[CutPlayer] = db.relationship(
        "CutPlayer", foreign_keys=[lower_seed_id], backref="lower_seed_matches"
    )
    corp_player: Mapped[CutPlayer] = db.relationship(
        "CutPlayer", foreign_keys=[corp_player_id], backref="corp_cut_matches"
    )
    runner_player: Mapped[CutPlayer] = db.relationship(
        "CutPlayer",
        foreign_keys=[runner_player_id],
        backref="runner_cut_matches",
    )

    def __repr__(self) -> str:
        return f"<CutMatch>: {self.cut_id} <Table> {self.table_number} - Result: {self.result}"
