from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()
cors = CORS()
oauth = OAuth()
