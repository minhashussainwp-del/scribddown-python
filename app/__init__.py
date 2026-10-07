"""Flask app factory for ScribdDown."""
import os
from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

from .models import Base

load_dotenv()

engine = None
Session = None


def get_engine():
    global engine
    if engine is None:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///scribddown.db")
        # Render-style postgres:// -> postgresql://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        engine = create_engine(db_url, pool_pre_ping=True)
    return engine


def get_session():
    global Session
    if Session is None:
        Session = scoped_session(sessionmaker(bind=get_engine()))
    return Session()


def get_setting(db, key: str, default: str = "") -> str:
    from .models import Setting
    row = db.get(Setting, key)
    return row.value if row else default


def set_setting(db, key: str, value: str):
    from .models import Setting
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["APP_URL"] = os.environ.get("APP_URL", "http://localhost:8000").rstrip("/")
    app.url_map.strict_slashes = False

    # Init DB tables
    Base.metadata.create_all(get_engine())

    # Seed on first run (empty settings table)
    from .models import Setting
    db = get_session()
    try:
        if db.query(Setting).count() == 0:
            from .seed import run_seed
            run_seed(db)
    finally:
        db.close()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if Session is not None:
            Session.remove()

    # Request-scoped DB + lang
    @app.before_request
    def before():
        from flask import request
        g.db = get_session()
        # lang from URL prefix /<lang>/...
        parts = request.path.strip("/").split("/")
        from .i18n import get_lang
        g.lang = get_lang(parts[0] if parts and parts[0] else None)

    from .routes import frontend, api, admin
    app.register_blueprint(frontend.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(admin.bp)

    return app
