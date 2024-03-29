from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from AlgoLaw_Website.AlgoLawWeb.models import User, datetime, ROLES
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField('שם משתמש',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('מייל',
                        validators=[DataRequired(), Email()])
    password = PasswordField('סיסמא', validators=[DataRequired()])
    role = SelectField('תפקיד', validators=[DataRequired()], choices=list(ROLES.keys()))
    confirm_password = PasswordField('חזור על סיסמא',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('הירשם')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(f'Username taken already please choose another')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(f'Email taken already please choose another')


class LoginForm(FlaskForm):
    email = StringField('מייל',
                        validators=[DataRequired(), Email()])
    password = PasswordField('סיסמא', validators=[DataRequired()])
    remember = BooleanField('זכור אותי')
    submit = SubmitField('!התחבר')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Proile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(f'Username taken already please choose another')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(f'Email taken already please choose another')


class CasesForm(FlaskForm):
    csv_file = FileField('Upload case CSV file', validators=[FileRequired()])
    submit = SubmitField('העלה')


class UploadFilesForm(FlaskForm):
    mishmoret_file = FileField('mishmoret CSV file', validators=[])
    rotation_file = FileField('rotation CSV file', validators=[])
    holidays_file = FileField('holidays CSV file', validators=[])
    new_cases_file = FileField('new cases CSV file', validators=[])
    submit = SubmitField('חלוקה ושיבוץ תיקים')


class VacaForm(FlaskForm):
    start_date = DateField('תחילת חופש', validators=[DataRequired()], format='%Y/%m/%d')
    end_date = DateField('סוף חופש', validators=[DataRequired()], format='%Y/%m/%d')
    submit = SubmitField('זמן חופשה')


class EventForm(FlaskForm):
    start_date = DateTimeField('תחילת אירוע', validators=[DataRequired()], format='YYYY/MM/DD hh:mm')
    end_date = DateTimeField('סוף אירוע', validators=[DataRequired()], format='YYYY/MM/DD hh:mm')
    submit = SubmitField('זמן אירוע')


class CaseSearchForm(FlaskForm):
    lawyer_id = StringField('מספר זיהוי העורך דין', validators=[])
    orer_id = StringField('מספר זיהוי העורר', validators=[])
    case_id = StringField('מספר תיק', validators=[])
    main_type = StringField('קטגוריה ראשית', validators=[])
    secondary_type = StringField('קטגוריה משנית', validators=[])
    submit = SubmitField('חיפוש')

class lawyerSearchForm(FlaskForm):
    lawyer_name = StringField('שם פרטי', validators=[])
    lawyer_last_name = StringField('שם משפחה', validators=[])
    lawyer_id = StringField('מספר זיהוי', validators=[])
    lawyer_mail = StringField('כתובת דואר אלקטרוני', validators=[])
    lawyer_phone = StringField('מספר טלפון', validators=[])
    submit = SubmitField('חיפוש')


class WeightForm(FlaskForm):
    type_1 = StringField('הסתננות ומקלט', validators=[])
    type_2 = StringField('רישום ילדים', validators=[])
    type_3 = StringField('הומניטרי', validators=[])
    type_4 = StringField('תושבות', validators=[])
    type_5 = StringField('איחוד משפחות', validators=[])
    type_6 = StringField('עבודה ולימודים', validators=[])
    type_7 = StringField('אזרחות', validators=[])
    type_8 = StringField('כללי', validators=[])
    type_9 = StringField('חוק השבות', validators=[])
    type_10 = StringField('כניסה וביקור', validators=[])
    submit = SubmitField('שנה')
