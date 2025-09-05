from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from data_models.match import MatchReport
from data_models.players import Player
from data_models.tournaments import Tournament
from data_models.model_store import db
import aesops.business_logic.players as p_logic
import aesops.business_logic.top_cut as tc_logic
import aesops.business_logic.tournament as t_logic
import aesops.business_logic.decklist as d_logic
from aesops.forms import (
    PlayerForm,
    TournamentForm,
)
from data_models.users import User
import aesops.business_logic.users as u_logic
from aesops.utility import (
    render_side_bias,
    format_results,
    get_faction,
    rank_tables,
)

tournament_blueprint = Blueprint("tournaments", __name__)


def redirect_for_tournament(tid):
    return redirect(url_for("tournaments.tournament", tid=tid))


@tournament_blueprint.route("/<int:tid>", methods=["GET", "POST"])
@tournament_blueprint.route("/tournament/<int:tid>", methods=["GET", "POST"])
@tournament_blueprint.route("/<int:tid>/standings", methods=["GET", "POST"])
def tournament(tid):
    tournament = Tournament.query.get(tid)

    # Rank the players in the tournament and calculate their info required
    # to be rendered on the page
    result = t_logic.calculate_player_ranks(tournament)

    # Generate the cut standings
    cut_standings = None
    if tournament.cut is not None:
        cut_standings = tc_logic.get_standings(tournament.cut)

    return render_template(
        "tournament.html",
        tournament=tournament,
        admin=u_logic.has_admin_rights(current_user, tid),
        render_side_bias=render_side_bias,
        get_faction=get_faction,
        t_logic=t_logic,
        cut_standings=cut_standings,
        result=result,
        p_logic=p_logic,
        last_concluded_round=(
            tournament.current_round
            if t_logic.is_current_round_finished(tournament)
            else tournament.current_round - 1
        ),
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
            require_decklist=form.require_decklist.data,
            require_login=form.require_login.data,
        )
        db.session.add(tournament)
        db.session.commit()
        flash(f"{tournament.name} has been created!", category="success")
        return redirect_for_tournament(tournament.id)
    return render_template("tournament_creation.html", form=form, heading="Create")


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
    form = PlayerForm(tournament=Tournament.query.get(tid))
    admin = u_logic.has_admin_rights(current_user, tid)
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
            fixed_table=form.fixed_table.data,
            table_number=form.table_number.data,
            uid=current_user.id if not current_user.is_anonymous else None,
        )
        db.session.add(player)
        db.session.commit()
        flash(f"{player.name} has been added!", category="success")
        return redirect_for_tournament(tid)
    tournament = Tournament.query.get(tid)
    return render_template(
        "player_registration.html", admin=admin, form=form, tournament=tournament
    )


def _render_round(tournament_: Tournament, rnd: int):
    return render_template(
        "round.html",
        tournament=tournament_,
        rnd=rnd,
        format_results=format_results,
        admin=u_logic.has_admin_rights(current_user, tournament_.id),
        rank_tables=rank_tables,
        get_faction=get_faction,
        t_logic=t_logic,
        match_report=MatchReport,
        has_reporting_rights=u_logic.has_reporting_rights,
    )


@tournament_blueprint.route("/<int:tid>/<int:rnd>", methods=["GET", "POST"])
def round(tid: int, rnd: int):
    tournament_ = Tournament.query.get(tid)
    return _render_round(tournament_, rnd)


@tournament_blueprint.route("/<int:tid>/current", methods=["GET", "POST"])
def round_current(tid: int):
    tournament_ = Tournament.query.get(tid)
    return _render_round(tournament_, tournament_.current_round)


@login_required
@tournament_blueprint.route("/<int:tid>/reveal_decklists", methods=["GET", "POST"])
def reveal_decklists(tid):
    tournament = Tournament.query.get(tid)
    if u_logic.has_admin_rights(current_user, tid) is False:
        flash("You do not have permission to reveal decklists for this tournament")
        return redirect_for_tournament(tournament.id)
    if tournament.reveal_decklists:
        flash("Making decklists private")
        tournament.reveal_decklists = False
        tournament.reveal_cut_decklists = False
    elif request.form.get("cut") == "cut":
        flash("Revealing cut decklists")
        tournament.reveal_decklists = False
        tournament.reveal_cut_decklists = True
    else:
        flash("Revealing all decklists")
        tournament.reveal_cut_decklists = True
        tournament.reveal_decklists = True
    db.session.add(tournament)
    db.session.commit()
    return redirect_for_tournament(tournament.id)


@tournament_blueprint.route("/<int:tid>/<int:pid>/decklists", methods=["GET", "POST"])
def display_decklist(tid, pid):
    tournament = Tournament.query.get(tid)
    player = Player.query.get(pid)
    if p_logic.reveal_decklists(
        player=player, tournament=tournament
    ) or u_logic.has_admin_rights(current_user, tid):
        return render_template(
            "decklist.html",
            tournament=tournament,
            player=player,
            admin=u_logic.has_admin_rights(current_user, tid),
            corp_deck=d_logic.generate_decklist_html(
                player.corp_deck, get_faction(player.corp)
            ),
            runner_deck=d_logic.generate_decklist_html(
                player.runner_deck, get_faction(player.runner)
            ),
            get_faction=get_faction,
        )
    else:
        flash("Decklists are not revealed for this tournament")
        return redirect_for_tournament(tournament.id)
