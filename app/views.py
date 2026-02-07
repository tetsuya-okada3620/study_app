from app.extensions import db, login_manager
from app.models import Users, Records, Categories, Foot

from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_required, login_user, logout_user, current_user
from app.forms import LoginForm, RecordForm, CategoryForm, SearchForm, FootForm
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from werkzeug.datastructures import MultiDict
from datetime import datetime, timedelta
import hashlib
import pandas as pd
import plotly.express as px

main = Blueprint("main", __name__)

@main.context_processor
def login_forms():
    user_id = current_user.user_id if current_user.is_authenticated else None
    username = current_user.name if current_user.is_authenticated else None
    return {"foot": FootForm(),
            "login": LoginForm(),
            "user_id": user_id,
            "username": username,
            }

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

@main.route("/", methods=["GET"])
def index():
    search = SearchForm(formdata=request.args)
    
    category_list = db.session.execute(select(Categories).order_by(Categories.category_id)).scalars().all()
    search.category_name.choices = [(str(v.category_id), v.category_name) for v in category_list]

    records = None
    if not request.args:
        # 初期化。とりあえず最新10件(ページネーションは今後の課題)
        search.category_name.data = "-998"
        stmt = select(Records).order_by(Records.study_date_start.desc()).limit(10)
        records = db.session.execute(stmt).scalars().all()

    elif search.validate():
        # 検索
        stmt = select(Records)
        # カテゴリ
        select_category = db.session.execute(select(Categories).where(Categories.category_id == int(search.category_name.data))).scalar_one_or_none()
        print(select_category)
        if select_category:
            if select_category.category_id == -999:  # すべて表示(明示的に)
                pass
            elif select_category.category_id == -998:  # 直近2週間
                stmt = stmt.where(Records.study_date_start >= (datetime.now() - timedelta(days=14)))
            else:  # 上記以外・DBに入っているカテゴリ
                stmt = stmt.where(Records.category_id == search.category_name.data)

        # 時間
        if search.study_date_start.data:
            stmt = stmt.where(Records.study_date_start >= search.study_date_start.data)
        if search.study_date_end.data:
            stmt = stmt.where(Records.study_date_start <= search.study_date_end.data)

        stmt = stmt.order_by(Records.study_date_start.desc())

        records = db.session.execute(stmt).scalars().all()

    # 時間(分)の合計値
    if records:
        study_duration_sum = sum([i.study_duration for i in records])
        study_hours = study_duration_sum // 60
        study_minutes = study_duration_sum % 60

        df = pd.DataFrame({"日付": [v.study_date_start.date() for v in records],
                           "時間(分)": [v.study_duration for v in records]}).sort_values(by="日付")
        df = df.groupby("日付").sum().reset_index()

        fig_html = px.bar(df, x="日付", y="時間(分)", text_auto="時間(分)", title="日毎推移").update_xaxes(
                                                                type="category",
                                                                tickformatstops=[
                                                                    dict(dtickrange=[None, "M1"], value="%m/%d"),
                                                                    dict(dtickrange=["M1", "Y1"], value="%Y"),
                                                                ]
                                                    ).to_html(full_html=False)
    else:
        study_hours = 0
        study_minutes = 0

    # print(search.errors)
    return render_template("index.html", records=records, search=search, study_hours=study_hours, study_minutes=study_minutes, fig_html=fig_html)

@main.route("/logout", methods=["POST"])
@login_required
def logout():
    flash("ログアウトしました")
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/login", methods=["POST"])
def login():
    forms = LoginForm()

    if forms.validate_on_submit():

        if forms.submit.data:
            username = forms.username.data
            password = forms.password.data
        elif forms.submit_guest.data:
            username = "guest"
            password = "guest"
        else:
            # 念の為。本来ならロギング処理。
            flash("不明なエラーです。管理者へお問い合わせください。")
            return redirect(url_for("main.index"))
            

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

@main.route("/delete_record", methods=["POST"])
@login_required
def delete_record():
    id = request.args.get("id")
    delete_id = db.session.get(Records, id)
    if delete_id:
        db.session.delete(delete_id)
        db.session.commit()

    return redirect(url_for("main.index"))

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

# # 足跡機能は一旦保留。 
# @main.route("/foot", methods=["POST"])
# def foot():
#     f_forms = FootForm()

#     # ipのDB格納は普通に考えて駄目なので、ハッシュ化して入れる。プロキシも考慮。
#     ip = request.headers.get("X-Forwarded-For", request.remote_addr)
#     hashed_ip = hashlib.sha256(ip.encode()).hexdigest()
    
#     if f_forms.validate_on_submit():
#         try:
#             db.session.add(Foot(hash=hashed_ip))
#             db.session.commit()
#             flash("ありがとうございます。とても嬉しいです。")
#         except IntegrityError:
#             db.session.rollback()
#             flash("ありがとうございます。とても嬉しいです。が足跡は1日1回です。。")

#     print(f_forms.errors)
#     return redirect(url_for("main.index"))