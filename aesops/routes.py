# Routes page for flask app
from aesops import app, db
from aesops.forms import (
    LoginForm,
    RegistrationForm,
    PlayerForm,
    TournamentForm,
    TournamentForm,
)
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from aesops.user import User
from pairing.tournament import Tournament


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    return render_template(
        "index.html", title="Home", tournaments=Tournament.query.all()
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("index"))
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username} has been registered!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/<int:tid>", methods=["GET", "POST"])
@app.route("/tournament/<int:tid>", methods=["GET", "POST"])
@app.route("/<int:tid>/standings", methods=["GET", "POST"])
def tournament(tid):
    return render_template("tournament.html", tournament=Tournament.query.get(tid))


@app.route("/create_tournament", methods=["GET", "POST"])
def create_tournament():
    form = TournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(
            name=form.name.data, date=form.date.data, description=form.description.data
        )
        db.session.add(tournament)
        db.session.commit()
        flash(f"{tournament.name} has been created!")
        return redirect(url_for("tournament", tid=tournament.id))
    return render_template("create_tournament.html")
