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
from pairing.player import Player
from pairing.match import Match, ConclusionError
import pairing.matchmaking as mm


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
            name=form.name.data,
            date=form.date.data,
            description=form.description.data,
            admin_id=current_user.id,
        )
        db.session.add(tournament)
        db.session.commit()
        flash(f"{tournament.name} has been created!")
        return redirect(url_for("tournament", tid=tournament.id))
    return render_template("tournament_creation.html", form=form)


@app.route("/<int:tid>/add_player", methods=["GET", "POST"])
def add_player(tid: int):
    form = PlayerForm()
    if form.validate_on_submit():
        player = Player(
            name=form.name.data,
            corp=form.corp.data,
            corp_deck=form.corp_deck.data,
            runner=form.runner.data,
            runner_deck=form.runner_deck.data,
            tid=tid,
            first_round_bye=form.bye.data,
        )
        db.session.add(player)
        db.session.commit()
        flash(f"{player.name} has been added!")
        return redirect(url_for("tournament", tid=tid))
    tournament = Tournament.query.get(tid)
    return render_template("player_registration.html", form=form, tournament=tournament)


@app.route("/<int:tid>/<int:rnd>", methods=["GET", "POST"])
def round(tid, rnd):
    tournament = Tournament.query.get(tid)

    def format_results(match: Match):
        if match.result is None:
            return ""
        if match.result == 1:
            return "3 - 0"
        if match.result == -1:
            return "0 - 3"
        if match.result == 0:
            return "1 - 1"

    return render_template(
        "round.html", tournament=tournament, rnd=rnd, format_results=format_results
    )


@app.route("/<int:tid>/<int:rnd>/<int:mid>/<int:result>", methods=["GET", "POST"])
def report_match(tid, rnd, mid, result):
    tournament = Tournament.query.get(tid)
    match = Match.query.get(mid)
    if match.result is None and current_user.is_anonymous:
        flash("You must be logged in to report a match with an existing result")
        return redirect(url_for("login"))
    if result == 2:
        match.runner_win()
        return redirect(url_for("round", tid=tid, rnd=rnd))
    if result == 1:
        match.corp_win()
        return redirect(url_for("round", tid=tid, rnd=rnd))
    if result == 0:
        match.tie()
        return redirect(url_for("round", tid=tid, rnd=rnd))
    return redirect(url_for("round", tournament=tournament, rnd=rnd))


@app.route("/<int:tid>/<int:rnd>/conclude", methods=["GET", "POST"])
def conclude_round(tid, rnd):
    tournament = Tournament.query.get(tid)
    try:
        tournament.conclude_round()
    except ConclusionError as e:
        flash(e)
        return redirect(url_for("round", tournament=tournament, rnd=rnd))
    return redirect(url_for("tournament", tid=tournament.id))


@login_required
@app.route("/<int:tid>/pair_round", methods=["GET", "POST"])
def pair_round(tid):
    tournament = Tournament.query.get(tid)
    mm.pair_round(tournament)
    return redirect(url_for("round", tid=tournament.id, rnd=tournament.current_round))


@login_required
@app.route("/<int:tid>/unpair_round", methods=["GET", "POST"])
def unpair_round(tid):
    tournament = Tournament.query.get(tid)
    tournament.unpair_round()
    return redirect(url_for("tournament", tid=tournament.id))
