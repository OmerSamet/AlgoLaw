from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'd1457561a9e312a6f439aa6185a41de2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config["OUTPUT_DIR"] = '/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from AlgoLawWeb import routes