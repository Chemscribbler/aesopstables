from aesops import db, login
from sqlalchemy.orm import Mapped
from pairing.tournament import Tournament
from aesops.user import User


class ToPref(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    tid: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("tournament.id"), nullable=False
    )
    allow_self_registration: Mapped[bool] = db.Column(db.Boolean, default=True)
    allow_self_results_report: Mapped[bool] = db.Column(db.Boolean, default=True)
    visible: Mapped[bool] = db.Column(db.Boolean, default=True)
