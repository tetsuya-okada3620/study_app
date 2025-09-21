from flask import Flask
from dotenv import load_dotenv
from app.extensions import db, login_manager
import os

def create_app():
    app = Flask(__name__)

    # 開発用。実際に運用する場合は、環境変数設定に直接記載すること。
    load_dotenv("config.env")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    login_manager.login_view = "main.login"
    login_manager.login_message = "先にログインしてください!"
    login_manager.session_protection = "strong"
    login_manager.init_app(app)

    app.secret_key = os.environ.get("SECRET_KEY")

    from app.views import main
    app.register_blueprint(main)

    return app