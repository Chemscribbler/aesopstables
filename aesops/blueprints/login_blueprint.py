from flask import Blueprint, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, current_user
from data_models.model_store import db
from aesops.forms import (
    LoginForm,
    RegistrationForm,
    UpdatePasswordForm,
)
import aesops.business_logic.users as u_logic
from data_models.users import User

login_blueprint = Blueprint("login", __name__)


@login_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not u_logic.check_password(user, form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login.login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("index"))
    return render_template("login.html", title="Sign In", form=form)


@login_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@login_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        u_logic.set_password(user, form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username} has been registered!", category="success")
        return redirect(url_for("login.login"))
    return render_template("register.html", title="Register", form=form)


@login_blueprint.route("/<int:uid>/reset_password", methods=["GET", "POST"])
def reset_password(uid):
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        user = User.query.get(uid)
        if not u_logic.check_password(user, form.old_password.data):
            flash("Incorrect password.")
            return redirect(url_for("login.reset_password", uid=uid))
        if form.old_password.data == form.new_password.data:
            flash("New password cannot be the same as old password.")
            return redirect(url_for("login.reset_password", uid=uid))
        else:
            u_logic.set_password(user, form.new_password.data)
            db.session.commit()
            flash("Password updated!", category="success")
            return redirect(url_for("index"))
    return render_template("reset_password.html", title="Reset Password", form=form)
