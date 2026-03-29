from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()


def init_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}})
