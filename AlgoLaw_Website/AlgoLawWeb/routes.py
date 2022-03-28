import os
import secrets
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from AlgoLawWeb import app, db, bcrypt
from AlgoLawWeb.forms import RegistrationForm, LoginForm, UpdateAccountForm, CasesForm, VacaForm
from AlgoLawWeb.models import User, Post, ROLES, JudgeToVaca
from flask_login import login_user, current_user, logout_user, login_required
import datetime
from AlgoLawBackEnd import judge_divider

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


@app.route('/<variable>/upload_generic', methods=['GET', 'POST'])
@login_required
def upload_generic(variable):
    form = CasesForm()
    if form.validate_on_submit():
        if form.csv_file.data:
            new_file = save_csv_file(form.csv_file.data)
            flash('File uploaded!', 'success')
            return redirect(url_for('home'))

    return render_template('upload_generic.html', title=variable, form=form)


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


###################################### SPECIFIC JUDGE CALENDAR FUNCTIONS ############################################
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


def check_date_earlier_than_today(form):
    if form.start_date.raw_data is not None:
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
        if start_date < datetime.datetime.today():
            flash('תאריך תחילת חופש צריך להיות לפחות היום או מאוחר יותר', 'danger')
            return False
    else:
        return False
    return True


def check_not_short_vaca(form):
    if form.start_date.raw_data is not None:
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
        delta = end_date - start_date
        if delta.days <= 3:
            flash('הבקשה היא לחופשה קצרה נא ללכת ל״חופשה קצרה״', 'warning')
            return False
    else:
        return False
    return True



@app.route('/judge_case_assignments', methods=['GET', 'POST'])
@login_required
def judge_case_assignments():
    return render_template('judge_case_assignments.html', events=events)


@app.route('/judge_short_vaca', methods=['GET', 'POST'])
@login_required
def judge_short_vaca():
    form = VacaForm()
    if check_date_earlier_than_today(form):
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
        delta = end_date - start_date
        if delta.days <= 3:
            vacation = JudgeToVaca(judge_id=current_user.id, is_verified=True, type='Short',
                                   start_date=start_date, end_date=end_date)
            add_to_db(vacation)
            flash('בקשה הוגשה', 'success')
            # finish
            return redirect(url_for('home'))
        else:
            flash('חופשה קצרה יכולה להיות עד 3 ימים, לחןפשה ארוכה יותר נע ללכת ל״בקשה לחופשה ארוכה״', 'danger')
    return render_template('judge_short_vaca.html', events=events, form=form)


@app.route('/judge_long_vaca', methods=['GET', 'POST'])
@login_required
def judge_long_vaca():
    form = VacaForm()
    if check_date_earlier_than_today(form):
        if check_not_short_vaca(form):
            start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
            vacation = JudgeToVaca(judge_id=current_user.id, is_verified=False, type='Long',
                                   start_date=start_date, end_date=end_date)
            add_to_db(vacation)
            flash('בקשה הוגשה', 'success')
            # finish
            return redirect(url_for('home'))

    return render_template('judge_long_vaca.html', events=events, form=form)

@app.route('/judge_case_search', methods=['GET', 'POST'])
@login_required
def judge_case_search():
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
    return render_template('judge_case_search.html', events=events)


@app.route('/judge_personal_space')
@login_required
def judge_personal_space():
    return render_template('judge_personal_space.html', title='Judge Personal Space', username=current_user.username)


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

###################################### SECRATARY FUNCTIONS ############################################

@app.route('/secretary_space')
@login_required
def secretary_space():
    return render_template('secretary_space.html', title='Secretary Space')


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################


###################################### RUN LOGIC ############################################

@app.route('/run_logic')
@login_required
def run_logic():
    judge_divider.handle_cases()
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
        'Name': 'Secretary Space',
        'redirect': 'secretary_space'
    },
    {
        'Name': 'Judge Personal Space',
        'redirect': 'judge_personal_space'
    }
]

@app.route('/')
@app.route('/home')
@login_required
def home():
    if check_logged_in():
        cur_role = ROLES[current_user.role]
        return return_role_page(cur_role)
    else:
        return redirect(url_for('login'))


#####################################################################################################################
#####################################################################################################################
#####################################################################################################################

###################################### LOGIN / LOGOUT FUNCTIONS #####################################################

def return_role_page(cur_role):
    if cur_role == 'Master':
        return render_template('home.html', buttons=buttons)
    elif cur_role == 'Judge':
        return judge_personal_space()
    elif cur_role == 'Secretary':
        return secretary_space()
    else:
        return render_template('home.html', buttons=buttons)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
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
