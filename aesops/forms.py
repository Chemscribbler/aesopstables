from flask_wtf import FlaskForm
from flask_wtf.form import _Auto
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    DateField,
    TextAreaField,
    IntegerField,
)
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError
from data_models.tournaments import Tournament
from aesops.utility import get_corp_ids, get_runner_ids
from data_models.users import User
from aesops.business_logic.decklist import decklist_parser


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


def validate_name(form, field):
    invalid_names = ["test", "admin", "(BYE)", "root"]
    if field.data in invalid_names:
        raise ValidationError("Invalid name. Please choose another.")


class PlayerForm(FlaskForm):
    def __init__(self, tournament=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tournament = tournament

    def validate_table_num(self, field):
        if self.fixed_table.data and field.data == 0:
            raise ValidationError(
                "If a Fixed Table is required, you must enter a Table Number."
            )

    def validate_decklist(self, field):
        if not self.tournament.require_decklist:
            return True
        if len(field.data) == 0:
            print("here")
            raise ValidationError("Decklist is required.")
        try:
            decklist_parser(field.data)
        except Exception as e:
            raise ValidationError(
                "Decklist is invalid. Make sure you're using Jinteki.net format."
                + str(e)
            )

    name = StringField("Player Name", validators=[DataRequired(), validate_name])
    corp = SelectField(
        "Corp ID",
        choices=[("", "Select Corp ID...")] + [(v, v) for v in get_corp_ids()],
        render_kw={"placeholder": "Select Corp ID..."},
        validators=[DataRequired("Corp ID missing")],
    )
    corp_deck = TextAreaField(
        "Corp Deck",
        validators=[validate_decklist],
        render_kw={"class": "decklist-entry"},
    )
    runner = SelectField(
        "Runner ID",
        choices=[("", "Select Runner ID...")] + [(v, v) for v in get_runner_ids()],
        render_kw={"placeholder": "Select Runner ID..."},
        validators=[DataRequired("Runner ID missing")],
    )
    runner_deck = TextAreaField(
        "Runner Deck",
        validators=[validate_decklist],
        render_kw={"class": "decklist-entry"},
    )
    pronouns = StringField("Pronouns")
    bye = BooleanField("First Round Bye")
    fixed_table = BooleanField(
        "Fixed Table Required?", render_kw={"onclick": "toggleElementChecked(event)"}
    )
    table_number = IntegerField(
        "Fixed Table Number",
        default=0,
        validators=[validate_table_num, NumberRange(min=0), Optional()],
    )
    submit = SubmitField("Add Player")


class TournamentForm(FlaskForm):
    name = StringField("Tournament Name", validators=[DataRequired()])
    date = DateField("Tournament Date", validators=[DataRequired()])
    description = TextAreaField("Tournament Description")
    allow_self_registration = BooleanField("Allow Self Registration", default=True)
    allow_self_results_report = BooleanField("Allow Self Results Report", default=True)
    visible = BooleanField("Visible", default=True)
    require_decklist = BooleanField("Require Decklist", default=False)
    submit = SubmitField("Submit")


class EditMatchesForm(FlaskForm):
    def validate_runner(self, field):
        if field.data and self.corp_player.data == field.data:
            raise ValidationError("Runner and Corp cannot be the same player.")

    table_number = IntegerField("Table Number", validators=[DataRequired()])
    corp_player = SelectField("Corp Player", validators=[DataRequired()])
    runner_player = SelectField(
        "Runner Player", validators=[DataRequired(), validate_runner]
    )
    submit = SubmitField("Save")

    def populate_players(self, players):
        self.corp_player.choices = [(p.id, p.name) for p in players]
        self.runner_player.choices = [(p.id, p.name) for p in players]
        self.runner_player.choices.append((None, "(BYE)"))


class UpdatePasswordForm(
    FlaskForm,
):
    def validate_new_password2(self, field):
        if self.new_password.data != field.data:
            raise ValidationError("New Passwords do not match.")

    old_password = PasswordField("Old Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    new_password2 = PasswordField(
        "Repeat New Password", validators=[DataRequired(), validate_new_password2]
    )
    submit = SubmitField("Save")
