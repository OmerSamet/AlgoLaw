from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
from AlgoLaw_Website.AlgoLawWeb.flask_celery import make_celery


app = Flask(__name__)
app.config['SECRET_KEY'] = 'd1457561a9e312a6f439aa6185a41de2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config["OUTPUT_DIR"] = os.path.join(app.root_path, 'DB_DATA')
app.config['CELERY_RESULT_BACKEND'] = 'db+sqlite:///site.db'
app.config['CELERY_BROKER_URL'] = 'amqp://localhost//'
celery = make_celery(app)
# email_watchdog = make_celery(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from AlgoLaw_Website.AlgoLawWeb import routes