from .model_store import db
from sqlalchemy.orm import Mapped


class Player(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String, nullable=False)
    pronouns: Mapped[str] = db.Column(db.String)
    corp: Mapped[str] = db.Column(db.String)
    runner: Mapped[str] = db.Column(db.String)
    corp_deck: Mapped[str] = db.Column(db.Text)
    runner_deck: Mapped[str] = db.Column(db.Text)
    active: Mapped[bool] = db.Column(db.Boolean, default=True)
    tid: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("tournament.id"), nullable=False
    )
    recieved_bye: Mapped[bool] = db.Column(db.Boolean, default=False)
    score: Mapped[int] = db.Column(db.Integer, default=0)
    games_played: Mapped[int] = db.Column(db.Integer, default=0)
    sos: Mapped[float] = db.Column(db.Numeric, default=0.0)
    esos: Mapped[float] = db.Column(db.Numeric, default=0.0)
    is_bye: Mapped[bool] = db.Column(db.Boolean, default=False)
    first_round_bye: Mapped[bool] = db.Column(db.Boolean, default=False)

    tournament = db.relationship("Tournament", back_populates="players")

    def __repr__(self) -> str:
        return f"<Player> {self.name}:{self.id} - Tournament {self.tid}"
