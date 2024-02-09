from .model_store import db
from data_models.tournaments import Tournament
from sqlalchemy.orm import Mapped
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    username: Mapped[bool] = db.Column(db.String, nullable=False)
    password_hash: Mapped[str] = db.Column(db.String, nullable=False)
    admin_rights: Mapped[bool] = db.Column(db.Boolean, default=False)
    email: Mapped[str] = db.Column(db.String, nullable=False)
    tournaments: Mapped["Tournament"] = db.relationship(
        "Tournament",
        backref="TO",
    )

    players = db.relationship("Player", back_populates="user")

    def __repr__(self) -> str:
        return f"<User> {self.username} {self.id}"
