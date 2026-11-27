import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from flask_login import LoginManager
from sqlalchemy import inspect, text
from config import Config
from database.db import db, seed_database
from models.user import User
from security import csrf

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get("SECRET_KEY") or len(app.config["SECRET_KEY"]) < 32:
        if os.environ.get("ALLOW_INSECURE_DEV", "").lower() != "true":
            raise RuntimeError("Set a random SECRET_KEY (at least 32 characters) in the environment.")
    csrf_secret = app.config.get("WTF_CSRF_SECRET_KEY")
    if not csrf_secret or csrf_secret == app.config.get("SECRET_KEY"):
        raise RuntimeError("Set a separate WTF_CSRF_SECRET_KEY; do not reuse SECRET_KEY.")
    if os.environ.get("RENDER") and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        raise RuntimeError("Set DATABASE_URL to PostgreSQL on Render; SQLite on Render Free is ephemeral.")

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.vehicles import vehicles_bp
    from routes.violations import violations_bp
    from routes.echallan import echallan_bp
    from routes.monitoring import monitoring_bp
    from routes.api import api_bp
    from routes.reports import reports_bp
    from routes.video_analysis import video_bp
    from routes.control import control_bp
    from models.device import Device

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(violations_bp)
    app.register_blueprint(echallan_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(control_bp)

    @app.get("/healthz")
    def healthz():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({"status": "ok", "database": "ok"}), 200
        except Exception:
            app.logger.exception("Health check database failure")
            return jsonify({"status": "degraded", "database": "unavailable"}), 503

    with app.app_context():
        db.create_all()
        # Safe additive migration for existing SQLite/PostgreSQL installations.
        inspector = inspect(db.engine)
        if "robot_devices" in inspector.get_table_names():
            columns = {c["name"] for c in inspector.get_columns("robot_devices")}
            with db.engine.begin() as conn:
                if "command_updated_at" not in columns:
                    conn.execute(text("ALTER TABLE robot_devices ADD COLUMN command_updated_at TIMESTAMP"))
                    conn.execute(text("UPDATE robot_devices SET command_updated_at = CURRENT_TIMESTAMP WHERE command_updated_at IS NULL"))
                if "command_seq" not in columns:
                    conn.execute(text("ALTER TABLE robot_devices ADD COLUMN command_seq INTEGER NOT NULL DEFAULT 0"))
                if "command_lease_at" not in columns:
                    conn.execute(text("ALTER TABLE robot_devices ADD COLUMN command_lease_at TIMESTAMP"))
                    conn.execute(text("UPDATE robot_devices SET command_lease_at = CURRENT_TIMESTAMP WHERE command_lease_at IS NULL"))
                if "rearm_required" not in columns:
                    conn.execute(text("ALTER TABLE robot_devices ADD COLUMN rearm_required BOOLEAN NOT NULL DEFAULT TRUE"))
        seed_database()
        # A process restart must never replay a previous movement or attachment command.
        for device in Device.query.all():
            device.command = "stop"
            device.command_updated_at = datetime.utcnow()
            device.command_lease_at = datetime.utcnow()
            device.rearm_required = True
            device.accessories = {"brush": False, "rig_up": False, "rig_down": False, "led": False, "spray": False}
            device.emergency_stop = False
        db.session.commit()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=os.environ.get("FLASK_DEBUG") == "1")
