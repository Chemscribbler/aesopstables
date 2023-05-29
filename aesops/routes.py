# Routes page for flask app
from aesops import app, db
from aesops.forms import (
    LoginForm,
    RegistrationForm,
    PlayerForm,
    TournamentForm,
    TournamentForm,
    EditMatchesForm,
)
from flask import render_template, flash, redirect, url_for, request, Response
from flask_login import current_user, login_user, logout_user, login_required
from aesops.user import User, has_admin_rights
from pairing.tournament import Tournament
from pairing.player import Player
from pairing.match import Match, ConclusionError
import pairing.matchmaking as mm
from aesops.utility import (
    display_side_bias,
    rank_tables,
    get_faction,
    format_results,
    get_json,
)
from top_cut.cut import Cut
from top_cut.elim_match import ElimMatch
import markdown


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
        flash(f"{user.username} has been registered!", category="success")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/<int:tid>", methods=["GET", "POST"])
@app.route("/tournament/<int:tid>", methods=["GET", "POST"])
@app.route("/<int:tid>/standings", methods=["GET", "POST"])
def tournament(tid):
    tournament = Tournament.query.get(tid)
    return render_template(
        "tournament.html",
        tournament=tournament,
        admin=has_admin_rights(current_user, tid),
        display_side_bias=display_side_bias,
        get_faction=get_faction,
        last_concluded_round=tournament.current_round
        if tournament.is_current_round_finished()
        else tournament.current_round - 1,
    )


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
        flash(f"{tournament.name} has been created!", category="success")
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
        flash(f"{player.name} has been added!", category="success")
        return redirect(url_for("tournament", tid=tid))
    tournament = Tournament.query.get(tid)
    return render_template("player_registration.html", form=form, tournament=tournament)


@app.route("/<int:tid>/<int:rnd>", methods=["GET", "POST"])
def round(tid, rnd):
    tournament = Tournament.query.get(tid)
    return render_template(
        "round.html",
        tournament=tournament,
        rnd=rnd,
        format_results=format_results,
        admin=has_admin_rights(current_user, tid),
        rank_tables=rank_tables,
        get_faction=get_faction,
    )


@app.route("/<int:tid>/<int:rnd>/<int:mid>/<int:result>", methods=["GET", "POST"])
def report_match(tid, rnd, mid, result):
    tournament = Tournament.query.get(tid)
    match = Match.query.get(mid)
    # if match.result is None and current_user.is_anonymous:
    #     flash("You must be logged in to report a match with an existing result")
    #     return redirect(url_for("login"))
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
        flash("Not all matches have been reported")
        return redirect(url_for("round", tid=tournament.id, rnd=rnd))
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


@login_required
@app.route("/<int:pid>/edit_player", methods=["GET", "POST"])
def edit_player(pid):
    player = Player.query.get(pid)
    tournament = player.tournament
    form = PlayerForm()
    if form.validate_on_submit():
        player.name = form.name.data
        player.corp = form.corp.data
        player.corp_deck = form.corp_deck.data
        player.runner = form.runner.data
        player.runner_deck = form.runner_deck.data
        player.first_round_bye = form.bye.data
        db.session.commit()
        flash(f"{player.name} has been edited!", category="success")
        return redirect(url_for("tournament", tid=player.tid))
    form.name.data = player.name
    form.corp.data = player.corp
    form.corp_deck.data = player.corp_deck
    form.runner.data = player.runner
    form.runner_deck.data = player.runner_deck
    form.bye.data = player.first_round_bye
    return render_template(
        "edit_player.html", tournament=tournament, form=form, player=player
    )


@login_required
@app.route("/<int:pid>/delete_player", methods=["GET", "POST"])
def delete_player(pid):
    player = Player.query.get(pid)
    if player.tournament.admin_id != current_user.id:
        flash("You do not have permission to delete this player")
        return redirect(url_for("tournament", tid=player.tid))
    if player.tournament.current_round > 0:
        flash("You cannot delete a player after the first round")
        return redirect(url_for("tournament", tid=player.tid))
    db.session.delete(player)
    db.session.commit()
    flash(f"{player.name} has been deleted!")
    return redirect(url_for("tournament", tid=player.tid))


@login_required
@app.route("/<int:pid>/drop_player", methods=["GET", "POST"])
def drop_player(pid):
    player = Player.query.get(pid)
    player.drop()
    flash(f"{player.name} has been dropped!")
    return redirect(url_for("tournament", tid=player.tid))


@login_required
@app.route("/<int:pid>/undrop_player", methods=["GET", "POST"])
def undrop_player(pid):
    player = Player.query.get(pid)
    player.undrop()
    flash(f"{player.name} has been undropped!")
    return redirect(url_for("tournament", tid=player.tid))


@login_required
@app.route("/delete_match/<mid>", methods=["GET", "POST"])
def delete_match(mid):
    match = Match.query.get(mid)
    round = match.rnd
    tid = match.tournament.id
    db.session.delete(match)
    db.session.commit()
    flash("Match deleted")
    return redirect(url_for("round", tid=tid, rnd=round))


@login_required
@app.route("/<int:tid>/<int:rnd>/edit_pairings", methods=["GET", "POST"])
def edit_pairings(tid, rnd):
    tournament = Tournament.query.get(tid)
    form = EditMatchesForm()
    if tournament.get_unpaired_players() is not None:
        form.populate_players(tournament.get_unpaired_players())
        if form.validate_on_submit():
            is_bye = form.runner_player.data == "None"
            print(is_bye)
            mm.create_match(
                tournament=tournament,
                corp_player=Player.query.get(form.corp_player.data),
                runner_player=Player.query.get(form.runner_player.data),
                is_bye=is_bye,
            )
            print(tournament.active_matches)

            return render_template(
                "edit_pairings.html",
                tournament=tournament,
                form=form,
                rnd=rnd,
                format_results=format_results,
                admin=has_admin_rights(current_user, tid),
                rank_tables=rank_tables,
                get_faction=get_faction,
            )
    return render_template(
        "edit_pairings.html",
        tournament=tournament,
        form=form,
        rnd=rnd,
        format_results=format_results,
        admin=has_admin_rights(current_user, tid),
        rank_tables=rank_tables,
        get_faction=get_faction,
    )


@app.route("/<int:tid>/create_cut", methods=["POST"])
def create_cut(tid):
    flash(
        f"Top {request.form.get('num_players')} and the format is {'Double Elim' if request.form.get('double_elim') else 'Single Elim'}"
    )
    tournament = Tournament.query.get(tid)
    num_players = request.form.get("num_players")
    double_elim = request.form.get("double_elim")
    c = Cut()
    double_elim = bool(int(double_elim))
    c.create(tournament, int(num_players), double_elim=double_elim)
    c.generate_round()
    return redirect(url_for("cut_round", tid=tournament.id, rnd=1))


@app.route("/<int:tid>/cut/<int:rnd>", methods=["GET", "POST"])
def cut_round(tid, rnd):
    tournament = Tournament.query.get(tid)
    return render_template(
        "cut_round.html",
        tournament=tournament,
        rnd=rnd,
        format_results=format_results,
        admin=has_admin_rights(current_user, tid),
        rank_tables=rank_tables,
        get_faction=get_faction,
    )


@login_required
@app.route("/<int:tid>/edit_cut", methods=["POST"])
def edit_cut(tid):
    result = request.form.get("result")
    action = request.form.get("action")
    mid = request.form.get("mid")
    rnd = request.form.get("rnd")
    cut = Tournament.query.get(tid).cut
    if result is not None:
        match = ElimMatch.query.get(mid)
        if result == "1":
            match.corp_win()
        elif result == "0":
            match.runner_win()
        else:
            raise ValueError(f"Invalid result {result == '1'}")
    elif action is None:
        raise ValueError("No action specified")
    else:
        if action == "delete":
            try:
                cut.delete_round(int(rnd))
            except ValueError as e:
                flash(
                    "To the first round use the delete cut button on the tournament page"
                )
            redirect(url_for("tournament", tid=tid))
        elif action == "swap":
            ElimMatch.query.get(mid).swap_sides()
        elif action == "pair_next":
            cut.conclude_round()
            db.session.refresh(cut)
            try:
                cut.generate_round()
            except ValueError as e:
                print(e)
                cut.rnd = cut.rnd - 1
                db.session.add(cut)
                db.session.commit()
                return redirect(url_for("tournament", tid=tid))
            redirect(url_for("cut_round", tid=tid, rnd=int(rnd) + 1))
        else:
            raise ValueError("Invalid action")
    return redirect(url_for("cut_round", tid=tid, rnd=cut.rnd))


@login_required
@app.route("/<int:tid>/delete_cut", methods=["POST"])
def delete_cut(tid):
    tournament = Tournament.query.get(tid)
    cut = Cut.query.get(tournament.cut.id)
    cut.destroy()
    return redirect(url_for("tournament", tid=tid))


@app.route("/<int:tid>/abr_export", methods=["GET"])
def abr_export(tid):
    response = Response(get_json(tid), mimetype="application/json")
    response.headers.set("Content-Disposition", "attachment", filename=f"{tid}.json")
    return response


@app.route("/about", methods=["GET"])
def about():
    with open("documentation/about.md", "r") as f:
        text = f.read()
        html = markdown.markdown(text)
    return render_template(
        "markdown_page.html", markdown_content=markdown.markdown(html)
    )


@app.route("/howto", methods=["GET"])
def howto():
    with open("documentation/howto.md", "r") as f:
        text = f.read()
        html = markdown.markdown(text)
    return render_template(
        "markdown_page.html", markdown_content=markdown.markdown(html)
    )
