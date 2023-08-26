from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app=app)
migrate = Migrate(app=app, db=db, render_as_batch=True)
login = LoginManager(app)
login.login_view = "login"

from aesops import routes
from data_models import model_store

from .blueprints.tournament_blueprint import tournament_blueprint
app.register_blueprint(tournament_blueprint)