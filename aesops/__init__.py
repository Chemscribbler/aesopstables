from flask import Flask
from config import Config
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)

app.config.from_object(Config)

from data_models.model_store import db
db.init_app(app)

from flask_celeryext import FlaskCeleryExt
from .distributed_logic.celery_controller import make_celery
ext_celery = FlaskCeleryExt(create_celery_app=make_celery)
ext_celery.init_app(app)

migrate = Migrate(app=app, db=db, render_as_batch=True)
login = LoginManager(app)
login.login_view = "login"

from aesops import routes
from data_models import model_store

# Import Views
from .blueprints.login_blueprint import login_blueprint
from .blueprints.markdown_blueprint import markdown_blueprint
from .blueprints.tournament_blueprint import tournament_blueprint
app.register_blueprint(login_blueprint)
app.register_blueprint(markdown_blueprint)
app.register_blueprint(tournament_blueprint)

# Import Distributed Logic
from .distributed_logic import player_dist