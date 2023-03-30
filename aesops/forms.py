from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    DateField,
    TextAreaField,
)
from wtforms.validators import DataRequired, ValidationError
from aesops.user import User
from aesops.utility import get_corp_ids, get_runner_ids


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class PlayerForm(FlaskForm):
    name = StringField("Player Name", validators=[DataRequired()])
    corp = SelectField("Corp ID", choices=get_corp_ids())
    corp_deck = TextAreaField("Corp Deck")
    runner = SelectField("Runner ID", choices=get_runner_ids())
    runner_deck = TextAreaField("Runner Deck")
    bye = BooleanField("First Round Bye")
    submit = SubmitField("Add Player")


class TournamentForm(FlaskForm):
    name = StringField("Tournament Name", validators=[DataRequired()])
    date = DateField("Tournament Date", validators=[DataRequired()])
    description = TextAreaField("Tournament Description")
    submit = SubmitField("Add Tournament")
