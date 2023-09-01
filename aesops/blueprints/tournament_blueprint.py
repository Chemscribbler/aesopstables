from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from data_models.players import Player
from data_models.tournaments import Tournament
from data_models.model_store import db
import aesops.business_logic.players as p_logic
import aesops.business_logic.tournament as t_logic
from aesops.forms import (
    PlayerForm,
    TournamentForm,
)
from data_models.users import User
import aesops.business_logic.users as u_logic
from aesops.utility import (
    display_side_bias,
    format_results,
    get_faction,
    rank_tables,
)

tournament_blueprint = Blueprint('tournaments', __name__)

def redirect_for_tournament(tid):
    return redirect(url_for("tournaments.tournament", tid=tid))

@tournament_blueprint.route("/<int:tid>", methods=["GET", "POST"])
@tournament_blueprint.route("/tournament/<int:tid>", methods=["GET", "POST"])
@tournament_blueprint.route("/<int:tid>/standings", methods=["GET", "POST"])
def tournament(tid):
    tournament = Tournament.query.get(tid)
    return render_template(
        "tournament.html",
        tournament=tournament,
        admin=u_logic.has_admin_rights(current_user, tid),
        display_side_bias=display_side_bias,
        get_faction=get_faction,
        t_logic=t_logic,
        p_logic=p_logic,
        last_concluded_round=tournament.current_round
        if t_logic.is_current_round_finished(tournament)
        else tournament.current_round - 1,
    )


@tournament_blueprint.route("/create_tournament", methods=["GET", "POST"])
def create_tournament():
    form = TournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(
            name=form.name.data,
            date=form.date.data,
            description=form.description.data,
            admin_id=current_user.id,
            allow_self_registration=form.allow_self_registration.data,
            allow_self_results_report=form.allow_self_results_report.data,
            visible=form.visible.data,
        )
        db.session.add(tournament)
        db.session.commit()
        flash(f"{tournament.name} has been created!", category="success")
        return redirect_for_tournament(tournament.id)
    return render_template("tournament_creation.html", form=form)


@login_required
@tournament_blueprint.route("/<int:tid>/delete", methods=["GET", "POST"])
def delete_tournament(tid):
    tournament = Tournament.query.get(tid)
    if u_logic.has_admin_rights(current_user, tid) is False:
        flash("You do not have permission to delete this tournament")
        return redirect_for_tournament(tournament.id)
    db.session.delete(tournament)
    db.session.commit()
    flash(f"{tournament.name} has been deleted!")
    return redirect(url_for("index"))


@tournament_blueprint.route("/<int:tid>/add_player", methods=["GET", "POST"])
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
            pronouns=form.pronouns.data,
        )
        db.session.add(player)
        db.session.commit()
        flash(f"{player.name} has been added!", category="success")
        return redirect_for_tournament(tid)
    tournament = Tournament.query.get(tid)
    return render_template("player_registration.html", form=form, tournament=tournament)


@tournament_blueprint.route("/<int:tid>/<int:rnd>", methods=["GET", "POST"])
def round(tid, rnd):
    tournament = Tournament.query.get(tid)
    return render_template(
        "round.html",
        tournament=tournament,
        rnd=rnd,
        format_results=format_results,
        admin=u_logic.has_admin_rights(current_user, tid),
        rank_tables=rank_tables,
        get_faction=get_faction,
        t_logic=t_logic,
    )
