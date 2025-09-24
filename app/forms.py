from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, TextAreaField, DateTimeLocalField, SelectField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")

class RecordForm(FlaskForm):
    id = HiddenField()
    category_name = SelectField("カテゴリ", validators=[DataRequired()])
    confirm = TextAreaField("内容", validators=[DataRequired()])
    study_date_start = DateTimeLocalField("開始日時", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    study_date_end = DateTimeLocalField("終了日時", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    remark = TextAreaField("備考")
    submit = SubmitField("送信")

class CategoryForm(FlaskForm):
    category_name = StringField("カテゴリ名", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("送信")

class SearchForm(FlaskForm):
    category_name = SelectField("カテゴリ", validators=[DataRequired()])
    study_date_start = DateTimeLocalField("開始日時")
    study_date_end = DateTimeLocalField("終了日時")
    submit = SubmitField("検索")