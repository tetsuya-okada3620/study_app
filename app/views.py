from app.extensions import db, login_manager
from app.models import Users, Records, Categories, Foot

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from app.forms import LoginForm, RecordForm, CategoryForm, SearchForm, FootForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import hashlib

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

@main.route("/", methods=["GET", "POST"])
def index():
    login = LoginForm()
    search = SearchForm()
    foot = FootForm()

    category_list = db.session.execute(select(Categories).order_by(Categories.category_id)).scalars().all()
    search.category_name.choices = [("-999", "すべて表示")] + [(str(v.category_id), v.category_name) for v in category_list]

    if request.method == "GET":
        search.category_name.data = "-999"
        now = datetime.now()
        search.study_date_start.data = datetime(year=now.year, month=now.month, day=now.day) - timedelta(days=7)
        search.study_date_end.data = datetime(year=now.year, month=now.month, day=now.day)

    records = None
    # 検索フォーム処理
    print(search.category_name.data)
    if search.validate_on_submit():
        stmt = select(Records)
        # カテゴリ
        select_category = db.session.execute(select(Categories).where(Categories.category_id == int(search.category_name.data))).scalar_one_or_none()
        print(select_category)
        if select_category:
            stmt = stmt.where(Records.category_id == search.category_name.data)
        # 時間
        if search.study_date_start.data:
            stmt = stmt.where(Records.study_date_start >= search.study_date_start.data)
        if search.study_date_end.data:
            stmt = stmt.where(Records.study_date_start <= search.study_date_end.data)

        records = db.session.execute(stmt).scalars().all()

    # print(search.errors)
    user_id = current_user.user_id if current_user.is_authenticated else None
    username = current_user.name if current_user.is_authenticated else None

    return render_template("index.html", records=records, login=login, search=search, foot=foot, user_id=user_id, username=username)

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

@main.route("/insert_category", methods=["GET", "POST"])
@login_required
def insert_category():
    c_forms = CategoryForm()
    if c_forms.validate_on_submit():
        print("OK")
        try:
            print(c_forms.category_name)
            db.session.add(Categories(category_name = c_forms.category_name.data))
            db.session.commit()
            flash(f"次のカテゴリを追加しました: {c_forms.category_name.data}")
        except IntegrityError:
            flash(f"「{c_forms.category_name.data}」のカテゴリは既に追加されています。")
            db.session.rollback()

    return redirect(url_for("main.input_record"))

@main.route("/input_record", methods=["GET", "POST"])
@login_required
def input_record():
    id = request.args.get("id")
    r_forms = RecordForm()
    c_forms = CategoryForm()

    # カテゴリリストの表示
    category_list = db.session.execute(select(Categories)).scalars().all()
    r_forms.category_name.choices = [(str(v.category_id), v.category_name) for v in category_list]

    if id and request.method == "GET":
        record = db.session.get(Records, int(id))
        r_forms.id.data = id
        r_forms.category_name.data = str(record.category_id)
        r_forms.confirm.data = record.confirm
        r_forms.study_date_start.data = record.study_date_start
        r_forms.study_date_end.data = record.study_date_end
        r_forms.remark.data = record.remark
    elif request.method == "GET":
        now = datetime.now()
        r_forms.study_date_start.data = datetime(year=now.year, month=now.month, day=now.day)
        r_forms.study_date_end.data = datetime(year=now.year, month=now.month, day=now.day)
        
    if r_forms.validate_on_submit():

        if r_forms.id.data:  # 編集
            record = db.session.get(Records, int(r_forms.id.data))
            record.confirm = r_forms.confirm.data
            record.study_date_start = r_forms.study_date_start.data
            record.study_date_end = r_forms.study_date_end.data
            record.remark = r_forms.remark.data
            record.category_id = int(r_forms.category_name.data)
        else:  # 新規登録
            record = Records(
                user_id = current_user.user_id,
                confirm = r_forms.confirm.data,
                study_date_start = r_forms.study_date_start.data,
                study_date_end = r_forms.study_date_end.data,
                write_date = datetime.now(),
                remark = r_forms.remark.data,
                category_id = int(r_forms.category_name.data)
            )
            db.session.add(record)
        db.session.commit()

        return redirect(url_for("main.index"))

    return render_template("input.html", r_forms=r_forms, c_forms=c_forms, id=id, username=current_user.name)

@main.route("/foot", methods=["POST"])
def foot():
    f_forms = FootForm()

    # ipのDB格納は普通に考えて駄目なので、ハッシュ化して入れる。プロキシも考慮。
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    hashed_ip = hashlib.sha256(ip.encode()).hexdigest()
    
    if f_forms.validate_on_submit():
        try:
            db.session.add(Foot(hash=hashed_ip))
            db.session.commit()
            flash("ありがとうございます。とても嬉しいです。")
        except IntegrityError:
            db.session.rollback()
            flash("ありがとうございます。とても嬉しいです。が足跡は1日1回です。。")

    print(f_forms.errors)
    return redirect(url_for("main.index"))