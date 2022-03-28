from datetime import datetime
from AlgoLawWeb import db, login_manager
from flask_login import UserMixin

ROLES = {
    'דיין/דיינת': 'Judge',
    'מזכיר/מזכירה': 'Secretary',
    'הנהלה': 'Master'
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    role = db.Column(db.String(20), nullable=False, default='None')

    def __repr__(self):
        return f"User:('{self.username}', '{self.email}', '{self.image_file}','{self.role}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post:('{self.title}', '{self.date_posted}')"


class JudgeToVaca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, nullable=False)
    type = db.Column(db.String(20), nullable=False)







class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=False)
    relevant_emails = db.Column(db.String(120), nullable=False)  # str of list of emails "['email1@gmail.com', 'email2@gmail.com',...]"
    datetime_of_event = db.Column(db.DateTime, nullable=False)
    def __repr__(self):
        return f"User:('{self.username}', '{self.email}', '{self.image_file}')"


class Judge(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    cases = db.relationship('Case', backref='Judge', lazy=True)
    locations = db.Column(db.String(120), nullable=False)  # str of list '[location1, location2 ...]'
    is_in_rotation = db.Column(db.Boolean, nullable=False)
    total_weight = db.Column(db.String(120), nullable=False)  # str of json '{location1: weight, location2: weight... '

    def __repr__(self):
        return f"User:('{self.username}', '{self.email}', '{self.image_file}')"


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_type = db.Column(db.String(100), nullable=False)
    second_type = db.Column(db.String(100), nullable=False)
    third_type = db.Column(db.String(100), nullable=True)
    urgency_level = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # 1 -> 15 minutes, 2 -> 30 minutes, 3 -> 45 minutes and so on
    location = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=False)

    def __repr__(self):
        return f"Post:('{self.title}', '{self.date_posted}')"
