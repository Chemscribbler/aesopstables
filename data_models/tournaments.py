from .model_store import db
from sqlalchemy.orm import Mapped


class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String, nullable=False)
    current_round = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime(timezone=True), default=db.func.now())
    description = db.Column(db.String)
    allow_self_registration: Mapped[bool] = db.Column(db.Boolean, default=True)
    allow_self_results_report: Mapped[bool] = db.Column(db.Boolean, default=True)
    visible: Mapped[bool] = db.Column(db.Boolean, default=True)
    require_decklist: Mapped[bool] = db.Column(db.Boolean, default=False)
    reveal_cut_decklists: Mapped[bool] = db.Column(db.Boolean, default=False)
    reveal_decklists: Mapped[bool] = db.Column(db.Boolean, default=False)

    players = db.relationship(
        "Player", back_populates="tournament", cascade="all, delete-orphan"
    )
    matches = db.relationship(
        "Match", back_populates="tournament", cascade="all, delete-orphan"
    )
    active_players = db.relationship(
        "Player",
        primaryjoin="and_(Tournament.id == Player.tid, Player.active==True)",
        viewonly=True,
    )
    active_matches = db.relationship(
        "Match",
        primaryjoin="and_(Tournament.id == Match.tid, Match.rnd == Tournament.current_round)",
        viewonly=True,
    )
    cut = db.relationship("Cut", uselist=False, back_populates="tournament")

    def __repr__(self) -> str:
        return f"<Tournament> {self.name}: {self.id}"
