# Routes page for flask app
from aesops import app
from data_models.model_store import db
from aesops.forms import (
    LoginForm,
    RegistrationForm,
    PlayerForm,
    TournamentForm,
    EditMatchesForm,
)
from flask import render_template, flash, redirect, url_for, request, Response
from flask_login import current_user, login_required
from data_models.exceptions import ConclusionError, PairingException
from data_models.match import Match, MatchReport
from data_models.players import Player
from data_models.top_cut import Cut, ElimMatch
from data_models.tournaments import Tournament
from data_models.users import User
import aesops.business_logic.elim_match as e_logic
import aesops.business_logic.match as m_logic
import aesops.business_logic.matchmaking as mm
import aesops.business_logic.players as p_logic
import aesops.business_logic.top_cut as tc_logic
import aesops.business_logic.tournament as t_logic
import aesops.business_logic.users as u_logic
from aesops.utility import (
    rank_tables,
    get_faction,
    format_results,
    get_json,
)


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    page = request.args.get("page", 1, type=int)
    tournament_page = (
        Tournament.query.filter_by(visible=True)
        .order_by(Tournament.date.desc())
        .paginate(
            page=page, per_page=app.config["TOURNAMENTS_PER_PAGE"], error_out=False
        )
    )

    next_url = (
        url_for("index", page=tournament_page.next_num)
        if tournament_page.has_next
        else None
    )
    prev_url = (
        url_for("index", page=tournament_page.prev_num)
        if tournament_page.has_prev
        else None
    )
    return render_template(
        "index.html",
        title="Home",
        tournaments=tournament_page,
        next_url=next_url,
        prev_url=prev_url,
    )


def redirect_for_tournament(tid):
    return redirect(url_for("tournaments.tournament", tid=tid))


def redirect_for_round(tid, rnd):
    return redirect(url_for("tournaments.round", tid=tid, rnd=rnd))


@app.route("/<int:tid>/<int:rnd>/<int:mid>/<int:result>", methods=["GET", "POST"])
def report_match(tid, rnd, mid, result):
    tournament = Tournament.query.get(tid)
    match = Match.query.get(mid)
    if (
        match.result is not None
        and u_logic.has_admin_rights(current_user, tid) is False
    ):
        flash("This match has already been reported - please contact the TO for edits")
        return redirect_for_round(tid=tournament.id, rnd=rnd)
    if result == MatchReport.RUNNER_WIN.value:
        m_logic.runner_win(match)
        return redirect_for_round(tid=tid, rnd=rnd)
    elif result == MatchReport.CORP_WIN.value:
        m_logic.corp_win(match)
        return redirect_for_round(tid=tid, rnd=rnd)
    elif result == MatchReport.DRAW.value:
        m_logic.tie(match)
        return redirect_for_round(tid=tid, rnd=rnd)
    elif result == MatchReport.INTENTIONAL_DRAW.value:
        m_logic.intentional_draw(match)
        return redirect_for_round(tid=tid, rnd=rnd)
    return redirect(url_for("tournaments.round", tournament=tournament, rnd=rnd))


@app.route("/<int:tid>/<int:rnd>/conclude", methods=["GET", "POST"])
def conclude_round(tid, rnd):
    tournament = Tournament.query.get(tid)
    try:
        t_logic.conclude_round(tournament)
    except ConclusionError as e:
        flash("Not all matches have been reported")
        return redirect_for_round(tid=tournament.id, rnd=rnd)
    return redirect_for_tournament(tournament.id)


@login_required
@app.route("/<int:tid>/pair_round", methods=["GET", "POST"])
def pair_round(tid):
    tournament = Tournament.query.get(tid)
    try:
        mm.pair_round(tournament)
    except PairingException as e:
        flash(str(e))
        return redirect_for_tournament(tournament.id)
    return redirect_for_round(tid=tournament.id, rnd=tournament.current_round)


@login_required
@app.route("/<int:tid>/unpair_round", methods=["GET", "POST"])
def unpair_round(tid):
    tournament = Tournament.query.get(tid)
    t_logic.unpair_round(tournament)
    return redirect_for_tournament(tournament.id)


@login_required
@app.route("/<int:pid>/edit_player", methods=["GET", "POST"])
def edit_player(pid):
    player = Player.query.get(pid)
    tournament = player.tournament
    form = PlayerForm(tournament=tournament)
    if form.validate_on_submit():
        player.name = form.name.data
        player.corp = form.corp.data
        player.corp_deck = form.corp_deck.data
        player.runner = form.runner.data
        player.runner_deck = form.runner_deck.data
        player.first_round_bye = form.bye.data
        player.pronouns = form.pronouns.data
        player.fixed_table = form.fixed_table.data
        if player.fixed_table:
            player.table_number = form.table_number.data
        else:
            player.table_number = 0
        db.session.commit()
        flash(f"{player.name} has been edited!", category="success")
        return redirect_for_tournament(player.tid)
    form.name.data = player.name
    form.corp.data = player.corp
    form.corp_deck.data = player.corp_deck
    form.runner.data = player.runner
    form.runner_deck.data = player.runner_deck
    form.bye.data = player.first_round_bye
    form.pronouns.data = player.pronouns
    form.fixed_table.data = player.fixed_table
    form.table_number.data = player.table_number
    return render_template(
        "player_registration.html",
        tournament=tournament,
        form=form,
        player=player,
        edit_player=True,
    )


@login_required
@app.route("/<int:pid>/delete_player", methods=["GET", "POST"])
def delete_player(pid):
    player = Player.query.get(pid)
    if player.tournament.admin_id != current_user.id:
        flash("You do not have permission to delete this player")
        return redirect_for_tournament(player.tid)
    if player.tournament.current_round > 0:
        flash("You cannot delete a player after the first round")
        return redirect_for_tournament(player.tid)
    db.session.delete(player)
    db.session.commit()
    flash(f"{player.name} has been deleted!")
    return redirect_for_tournament(player.tid)


@login_required
@app.route("/<int:pid>/drop_player", methods=["GET", "POST"])
def drop_player(pid):
    player = Player.query.get(pid)
    p_logic.drop(player)
    flash(f"{player.name} has been dropped!")
    return redirect_for_tournament(player.tid)


@login_required
@app.route("/<int:pid>/undrop_player", methods=["GET", "POST"])
def undrop_player(pid):
    player = Player.query.get(pid)
    p_logic.undrop(player)
    flash(f"{player.name} has been undropped!")
    return redirect_for_tournament(player.tid)


@login_required
@app.route("/delete_match/<mid>", methods=["GET", "POST"])
def delete_match(mid):
    match = Match.query.get(mid)
    round = match.rnd
    tid = match.tournament.id
    db.session.delete(match)
    db.session.commit()
    flash("Match deleted")
    return redirect(url_for("tournaments.round", tid=tid, rnd=round))


@login_required
@app.route("/<int:tid>/<int:rnd>/edit_pairings", methods=["GET", "POST"])
def edit_pairings(tid, rnd):
    tournament = Tournament.query.get(tid)
    form = EditMatchesForm()
    if t_logic.get_unpaired_players(tournament) is not None:
        form.populate_players(t_logic.get_unpaired_players(tournament))
        if form.validate_on_submit():
            is_bye = form.runner_player.data == "None"
            print(is_bye)
            mm.create_match(
                tournament=tournament,
                corp_player=Player.query.get(form.corp_player.data),
                runner_player=None
                if is_bye
                else Player.query.get(form.runner_player.data),
                is_bye=is_bye,
                table_number=form.table_number.data,
            )
            print(tournament.active_matches)

            return render_template(
                "edit_pairings.html",
                tournament=tournament,
                form=form,
                rnd=rnd,
                format_results=format_results,
                admin=u_logic.has_admin_rights(current_user, tid),
                rank_tables=rank_tables,
                get_faction=get_faction,
                t_logic=t_logic,
                match_report=MatchReport,
            )
    return render_template(
        "edit_pairings.html",
        tournament=tournament,
        form=form,
        rnd=rnd,
        format_results=format_results,
        admin=u_logic.has_admin_rights(current_user, tid),
        rank_tables=rank_tables,
        get_faction=get_faction,
        t_logic=t_logic,
        match_report=MatchReport,
    )


@app.route("/<int:tid>/create_cut", methods=["POST"])
def create_cut(tid):
    tournament = Tournament.query.get(tid)
    num_players = request.form.get("num_players")
    double_elim = request.form.get("double_elim")
    c = Cut()
    double_elim = bool(int(double_elim))
    try:
        tc_logic.create(c, tournament, int(num_players), double_elim=double_elim)
        tc_logic.generate_round(c)
        flash(
            f"Top {request.form.get('num_players')} and the format is {'Double Elim' if request.form.get('double_elim') else 'Single Elim'}"
        )
        return redirect(url_for("cut_round", tid=tournament.id, rnd=1))
    except Exception as e:
        flash(str(e))
        db.session.delete(c)
        db.session.commit()
        return redirect_for_tournament(tournament.id)


@app.route("/<int:tid>/cut/<int:rnd>", methods=["GET", "POST"])
def cut_round(tid, rnd):
    tournament = Tournament.query.get(tid)
    return render_template(
        "cut_round.html",
        tournament=tournament,
        rnd=rnd,
        format_results=format_results,
        admin=u_logic.has_admin_rights(current_user, tid),
        rank_tables=rank_tables,
        get_faction=get_faction,
        tc_logic=tc_logic,
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
            e_logic.corp_win(match)
        elif result == "0":
            e_logic.runner_win(match)
        else:
            raise ValueError(f"Invalid result {result == '1'}")
    elif action is None:
        raise ValueError("No action specified")
    else:
        if action == "delete":
            try:
                tc_logic.delete_round(cut, int(rnd))
            except ValueError as e:
                flash(
                    "To the first round use the delete cut button on the tournament page"
                )
            redirect_for_tournament(tid)
        elif action == "swap":
            e_logic.swap_sides(ElimMatch.query.get(mid))
        elif action == "pair_next":
            tc_logic.conclude_round(cut)
            db.session.refresh(cut)
            try:
                tc_logic.generate_round(cut)
            except ValueError as e:
                print(e)
                cut.rnd = cut.rnd - 1
                db.session.add(cut)
                db.session.commit()
                return redirect_for_tournament(tid)
            redirect(url_for("cut_round", tid=tid, rnd=int(rnd) + 1))
        else:
            raise ValueError("Invalid action")
    return redirect(url_for("cut_round", tid=tid, rnd=cut.rnd))


@login_required
@app.route("/<int:tid>/delete_cut", methods=["POST"])
def delete_cut(tid):
    tournament = Tournament.query.get(tid)
    cut = Cut.query.get(tournament.cut.id)
    tc_logic.destroy(cut)
    return redirect_for_tournament(tid)


@app.route("/<int:tid>/abr_export", methods=["GET"])
def abr_export(tid):
    response = Response(get_json(tid), mimetype="application/json")
    response.headers.set("Content-Disposition", "attachment", filename=f"{tid}.json")
    return response


@login_required
@app.route("/<int:uid>/tournaments", methods=["GET"])
def user_tournaments(uid):
    user = User.query.get(uid)
    tournaments = Tournament.query.filter_by(admin_id=uid).all()
    return render_template("user_tournaments.html", user=user, tournaments=tournaments)


@login_required
@app.route("/<int:tid>/edit", methods=["GET", "POST"])
def edit_tournament(tid):
    if u_logic.has_admin_rights(current_user, tid) is False:
        flash("You do not have permission to edit this tournament")
        return redirect_for_tournament(tid)
    tournament = Tournament.query.get(tid)
    form = TournamentForm()
    if form.validate_on_submit():
        tournament.name = form.name.data
        tournament.date = form.date.data
        tournament.description = form.description.data
        tournament.allow_self_registration = form.allow_self_registration.data
        tournament.allow_self_results_report = form.allow_self_results_report.data
        tournament.require_login = form.require_login.data
        tournament.visible = form.visible.data
        tournament.require_decklist = form.require_decklist.data
        db.session.commit()
        flash(f"{tournament.name} has been edited!", category="success")
        return redirect_for_tournament(tournament.id)
    form.name.data = tournament.name
    form.date.data = tournament.date
    form.description.data = tournament.description
    form.allow_self_registration.data = tournament.allow_self_registration
    form.allow_self_results_report.data = tournament.allow_self_results_report
    form.visible.data = tournament.visible
    form.require_decklist.data = tournament.require_decklist
    return render_template(
        "tournament_creation.html", form=form, tournament=tournament, heading="Edit"
    )
