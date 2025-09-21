from app.extensions import db, login_manager
from app.models import Users, Records

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from app.forms import LoginForm, RecordForm
from sqlalchemy import select
from werkzeug.security import check_password_hash
from datetime import datetime

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

@main.route("/", methods=["GET", "POST"])
def index():
    login = LoginForm()

    # このままだと全て出力なので、検索で出力するように調整すること。
    user_id = current_user.user_id if current_user.is_authenticated else None
    username = current_user.name if current_user.is_authenticated else None
    records = db.session.execute(select(Records)).scalars().all()

    return render_template("index.html", records=records, login=login, user_id=user_id, username=username)


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    flash("ログアウトしました")
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/login", methods=["GET", "POST"])
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
            flash("ログインしました。")
    
    return redirect(url_for("main.index"))


@main.route("/input_record", methods=["GET", "POST"])
@login_required
def input_record():
    id = request.args.get("id")
    forms = RecordForm()
    print(id)

    if id and request.method == "GET":
        record = db.session.get(Records, int(id))
        forms.id.data = id
        forms.confirm.data = record.confirm
        forms.study_date_start.data = record.study_date_start
        forms.study_date_end.data = record.study_date_end
        forms.remark.data = record.remark
        
    print(forms.id.data)
    print(forms.errors)
    print(forms.validate_on_submit())
    if forms.validate_on_submit():

        if forms.id.data:  # 編集
            print("編集")
            record = db.session.get(Records, int(forms.id.data))
            record.confirm = forms.confirm.data
            record.study_date_start = forms.study_date_start.data
            record.study_date_end = forms.study_date_end.data
            record.remark = forms.remark.data
        else:  # 新規登録
            print("新規登録")
            record = Records(
                user_id=current_user.user_id,
                confirm=forms.confirm.data,
                study_date_start=forms.study_date_start.data,
                study_date_end=forms.study_date_end.data,
                write_date=datetime.now(),
                remark=forms.remark.data
            )
            db.session.add(record)
        db.session.commit()

        return redirect(url_for("main.index"))

    return render_template("input.html", forms=forms, id=id, username=current_user.name)
