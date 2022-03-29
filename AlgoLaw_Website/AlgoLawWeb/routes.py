import secrets
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from AlgoLawWeb import app, db, bcrypt
from AlgoLawWeb.forms import RegistrationForm, LoginForm, UpdateAccountForm, CasesForm, VacaForm
from AlgoLawWeb.models import User, Post, ROLES, JudgeToVaca
from flask_login import login_user, current_user, logout_user, login_required
import datetime
from AlgoLawBackEnd import judge_divider
from AlgoLawWeb.utilities import check_if_already_vacation, save_csv_file, \
    get_all_vacations, get_all_judges, check_date_earlier_than_today, check_not_short_vaca, add_to_db, check_logged_in, \
    return_role_page


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


@app.route('/master_space')
@login_required
def master_space():
    return render_template('master_space.html', title='Master Space', username=current_user.username)


@app.route('/master_vacation_view')
@login_required
def master_vacation_view():
    vacations = get_all_vacations()
    judges = get_all_judges()
    return render_template('master_vacation_view.html', title='Vacations View',
                           username=current_user.username, events=vacations,
                           judges=judges)


@app.route('/judge_case_assignments', methods=['GET', 'POST'])
@login_required
def judge_case_assignments():
    return render_template('judge_case_assignments.html', events=events)


@app.route('/judge_short_vaca', methods=['GET', 'POST'])
@login_required
def judge_short_vaca():
    form = VacaForm()
    vacations = get_all_vacations(judge_id=current_user.id)
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
    return render_template('judge_short_vaca.html', events=vacations, form=form)


@app.route('/judge_long_vaca', methods=['GET', 'POST'])
@login_required
def judge_long_vaca():
    form = VacaForm()
    vacations = get_all_vacations(judge_id=current_user.id)
    if check_date_earlier_than_today(form):
        if check_not_short_vaca(form):
            start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
            if not check_if_already_vacation(start_date, end_date, current_user.id):
                vacation = JudgeToVaca(judge_id=current_user.id, is_verified=False, type='Long',
                                   start_date=start_date, end_date=end_date)
                add_to_db(vacation)
                flash('בקשה הוגשה', 'success')
                # finish
                return redirect(url_for('home'))

    return render_template('judge_long_vaca.html', events=vacations, form=form)


@app.route('/judge_case_search', methods=['GET', 'POST'])
@login_required
def judge_case_search():
    return render_template('judge_case_search.html', events=events)


@app.route('/judge_personal_space')
@login_required
def judge_personal_space():
    return render_template('judge_personal_space.html', title='Judge Personal Space', username=current_user.username)


@app.route('/secretary_space')
@login_required
def secretary_space():
    return render_template('secretary_space.html', title='Secretary Space')


@app.route('/run_logic')
@login_required
def run_logic():
    judge_divider.handle_cases()
    output_file = 'output.csv'
    return send_from_directory(directory=app.config["OUTPUT_DIR"], path=output_file, as_attachment=True)


@app.route('/')
@app.route('/home')
@login_required
def home():
    if check_logged_in():
        cur_role = ROLES[current_user.role]
        role_page_id = return_role_page(cur_role)
        if role_page_id == 1:
            return master_space()
        elif role_page_id == 2:
            return judge_personal_space()
        elif role_page_id == 3:
            return secretary_space()
        else:
            return render_template('home.html', buttons=buttons)
    else:
        return redirect(url_for('login'))


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
