from aesops import db, login
from sqlalchemy.orm import Mapped
from pairing.tournament import Tournament
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
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

    def __repr__(self) -> str:
        return f"<User> {self.username} {self.id}"

    def create_tournament(self, name, date=date.today()):
        t = Tournament(name=name, date=date, admin_id=self.id)
        db.session.add(t)
        db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_admin_rights(self, tid):
        t = Tournament.query.get(tid)
        if t.admin_id == self.id or self.admin_rights:
            return True
        else:
            return False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
