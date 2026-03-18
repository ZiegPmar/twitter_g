from flask import Flask
from . import db

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE="data/app.db"
    )

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app