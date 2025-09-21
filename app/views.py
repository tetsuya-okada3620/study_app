from app.extensions import db, login_manager
from app.models import Users

from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, login_user, logout_user, current_user
from app.forms import LoginForm
from sqlalchemy import select
from werkzeug.security import check_password_hash

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

@login_required
@main.route("/logout", methods=["POST"])
def logout():
    flash("ログアウトしました")
    logout_user()
    return redirect(url_for("main.login"))

@main.route("/", methods=["GET", "POST"])
def login():
    forms = LoginForm()

    if forms.validate_on_submit():
        username = forms.username.data
        password = forms.password.data

        stmt = select(Users).where(Users.name == username)
        search_account = db.session.execute(stmt).scalars().first()  # Users.nameはユニーク前提とします。

        if search_account is None or not check_password_hash(search_account.password, password):
            flash("ユーザー名またはパスワードが間違っています。")
        else:
            login_user(search_account)
            return redirect(url_for("main.index"))

    return render_template("login.html", forms=forms)


@main.route("/index")
@login_required
def index():
    return render_template("index.html", username=current_user.name)