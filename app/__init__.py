from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app=app)
migrate = Migrate(app=app, db=db, render_as_batch=True)

from app import routes, models
