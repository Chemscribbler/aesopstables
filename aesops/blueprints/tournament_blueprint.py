from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from data_models.tournaments import Tournament
from aesops import db
import aesops.business_logic.tournament as t_logic
from aesops.forms import (
    TournamentForm,
)
from aesops.user import User, has_admin_rights
from aesops.utility import (
    display_side_bias,
    get_faction,
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
        admin=has_admin_rights(current_user, tid),
        display_side_bias=display_side_bias,
        get_faction=get_faction,
        t_logic=t_logic,
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

