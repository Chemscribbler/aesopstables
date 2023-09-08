from aesops import app
from data_models.model_store import db
from data_models.match import Match
from data_models.players import Player
from data_models.tournaments import Tournament
from data_models.users import User


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Player": Player,
        "Tournament": Tournament,
        "Match": Match,
    }
