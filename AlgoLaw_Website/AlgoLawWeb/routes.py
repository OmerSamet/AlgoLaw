import os
import secrets
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from AlgoLawWeb import app, db, bcrypt
from AlgoLawWeb.forms import RegistrationForm, LoginForm, UpdateAccountForm, CasesForm
from AlgoLawWeb.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime


###################################### UPLOAD FUNCTIONS #############################################################

def check_available_directory():
    current_year = datetime.now().year
    current_quarter = (datetime.now().month - 1 // 3) + 1
    if not os.path.isdir(f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}'):
        os.mkdir(f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}')
    return f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}'


def save_csv_file(form_csv_file):
    output_dir = check_available_directory()
    uploader_username = current_user.username
    csv_path = os.path.join(app.root_path, output_dir, uploader_username+'_Case_Data.csv')
    form_csv_file.save(csv_path)
    return csv_path


@app.route('/upload_cases', methods=['GET', 'POST'])
@login_required
def upload_cases():
    form = CasesForm()
    if form.validate_on_submit():
        if form.csv_file.data:
            new_file = save_csv_file(form.csv_file.data)
            flash('File uploaded!', 'success')
            return redirect(url_for('home'))

    return render_template('upload_cases.html', title='Upload Cases', form=form)


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


###################################### SPECIFIC JUDGE CALENDAR FUNCTIONS ############################################

@app.route('/judge_case_assignments', methods=['GET', 'POST'])
@login_required
def judge_case_assignments():
    events = [
        {
            'todo': 'my event1',
            'date': '2022-01-30',
        },
        {
            'todo': 'my event2',
            'date': '2022-01-31',
        }
    ]
    return render_template('judge_case_assignments.html', events=events)


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


###################################### RUN LOGIC ############################################

@app.route('/run_logic')
@login_required
def run_logic():
    output_file = 'output.csv'
    return send_from_directory(directory=app.config["OUTPUT_DIR"], path=output_file, as_attachment=True)


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################



###################################### UTILITY FUNCTIONS #############################################################

def check_logged_in():
    if current_user.is_authenticated:
        return True
    else:
        return False


def add_to_db(data_to_add):
    db.session.add(data_to_add)
    db.session.commit()


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


###################################### HOME FUNCTIONS #############################################################

buttons = [
    {
        'Name': 'Upload New Cases',
        'redirect': 'upload_cases'
    },
    {
        'Name': 'Get Case Assignments',
        'redirect': 'judge_case_assignments'
    },
    {
        'Name': 'Run Logic',
        'redirect': 'run_logic'
    },
    {
        'Name': 'Find Cases',
        'redirect': 'home'
    },
    {
        'Name': 'Input Judge missing days',
        'redirect': 'home'
    }
]


@app.route('/')
@app.route('/home')
@login_required
def home():
    if check_logged_in():
        return render_template('home.html', buttons=buttons)
    else:
        return redirect(url_for('login'))


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

###################################### LOGIN / LOGOUT FUNCTIONS #####################################################

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        add_to_db(user)
        flash(f'Your account has been created! You can now login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Login check
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

#####################################################################################################################
#####################################################################################################################
#####################################################################################################################
