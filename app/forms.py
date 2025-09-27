from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, TextAreaField, DateTimeLocalField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")

class RecordForm(FlaskForm):
    id = HiddenField()
    category_name = SelectField("カテゴリ", validators=[DataRequired()])
    confirm = TextAreaField("内容", validators=[DataRequired()])
    study_date_start = DateTimeLocalField("開始日時", format="%Y-%m-%dT%H:%M")
    study_date_end = DateTimeLocalField("終了日時", format="%Y-%m-%dT%H:%M")
    remark = TextAreaField("備考")
    submit = SubmitField("送信")

class CategoryForm(FlaskForm):
    category_name = StringField("カテゴリ名", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("送信")

class SearchForm(FlaskForm):
    class Meta:
        csrf = False
    category_name = SelectField("カテゴリ", validators=[DataRequired()])
    study_date_start = DateTimeLocalField("開始日時", validators=[Optional()])
    study_date_end = DateTimeLocalField("終了日時", validators=[Optional()])
    submit = SubmitField("検索")

class FootForm(FlaskForm):
    submit = SubmitField("足跡を残す")