from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, TextAreaField, DateTimeLocalField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")

class RecordForm(FlaskForm):
    id = HiddenField()
    confirm = TextAreaField("内容", validators=[DataRequired()])
    study_date_start = DateTimeLocalField("開始日時", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    study_date_end = DateTimeLocalField("終了日時", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    remark = TextAreaField("備考")
    submit = SubmitField("送信")