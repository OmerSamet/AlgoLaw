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


class Vacation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, nullable=False)
    type = db.Column(db.String(20), nullable=False)


class SickDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, nullable=False)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=False)
    relevant_emails = db.Column(db.String(120), nullable=False)  # str of list of emails "['email1@gmail.com', 'email2@gmail.com',...]"
    datetime_of_event = db.Column(db.DateTime, nullable=False)


class Judge(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    cases = db.relationship('Case', backref='Judge', lazy=True)
    locations = db.Column(db.String(120), nullable=False)  # str of list '[location1, location2 ...]'
    is_in_rotation = db.Column(db.Boolean, nullable=False)
    total_weight = db.Column(db.String(120), nullable=False)  # str of json '{location1: weight, location2: weight... '
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Hall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hall_number = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(40), nullable=False)


class Rotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_type = db.Column(db.String(100), nullable=False)
    second_type = db.Column(db.String(100), nullable=False)
    third_type = db.Column(db.String(100), nullable=True)
    urgency_level = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Int of how many minutes
    location = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    quarter_created = db.Column(db.String(20), nullable=False)
    year_created = db.Column(db.String(20), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=True)
    is_done = db.Column(db.Boolean, nullable=False, default=False)  # has this case been done yet?


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    quarter = db.Column(db.String(20), nullable=False)
    year = db.Column(db.String(20), nullable=False)


class MeetingSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)  # id of hall and location in hall table
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # actual date of schedule
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'),
                         nullable=True)  # Nullable so we can add cases before division
    # start_time and end_time hold str of only the hours to be turned to datetime with date from HallSchedule
    start_time = db.Column(db.String(100), nullable=True)  # datetime.now().strftime("%H:%M") -> 09:30
    end_time = db.Column(db.String(100), nullable=True)  # datetime.now().strftime("%H:%M") -> 09:30
    is_verified = db.Column(db.Boolean, nullable=False, default=False)


class CaseJudgeLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=False)
    location = db.Column(db.String(20), nullable=False)
    quarter = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)