from aesops import login
from data_models.model_store import db
from data_models.tournaments import Tournament
from data_models.users import User
from data_models.match import Match
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash


def create_tournament(user: User, name, date=date.today()):
    t = Tournament(name=name, date=date, admin_id=user.id)
    db.session.add(t)
    db.session.commit()


def set_password(user: User, password):
    user.password_hash = generate_password_hash(password)


def check_password(user: User, password):
    return check_password_hash(user.password_hash, password)


def has_admin_rights(user: User, tid):
    if user.is_anonymous:
        return False
    if user.admin_rights:
        return True

    t = Tournament.query.get(tid)
    if t.admin_id == user.id:
        return True
    return False


def has_reporting_rights(user: User, mid: int):
    if user.is_anonymous:
        return False
    if user.admin_rights:
        return True
    match = Match.query.get(mid)
    if match.concluded:
        return False
    corp_player = match.corp_player
    runner_player = match.runner_player
    if corp_player.uid == user.id or runner_player.uid == user.id:
        return True
    return False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
