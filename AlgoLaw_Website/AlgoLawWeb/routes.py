from flask import render_template, url_for, flash, redirect, send_from_directory
from AlgoLawWeb import app, db, bcrypt
from AlgoLawWeb.forms import RegistrationForm, LoginForm, CasesForm, VacaForm, UploadFilesForm
from AlgoLawWeb.models import User, ROLES, Vacation, Judge, Hall
from flask_login import login_user, current_user, logout_user, login_required
import datetime
from AlgoLawWeb.AlgoLawBackEnd import judge_divider
from AlgoLawWeb.utilities import check_if_already_vacation, save_csv_file, \
    get_all_relevant_judges, check_date_earlier_than_today, check_not_short_vaca, add_to_db, check_logged_in, \
    return_role_page, insert_output_to_db, get_all_events, load_cases_to_db, load_holidays_to_db, load_rotations_to_db, \
    load_mishmoret_to_db, get_upload_div_colors
import json
from AlgoLawWeb.db_initiator import DBInitiator
from AlgoLawWeb.scheduler import run_division_logic
import os


@app.route('/upload_cases', methods=['GET', 'POST'])
@login_required
def upload_cases():
    form = CasesForm()
    if form.validate_on_submit():
        if form.csv_file.data:
            new_file = save_csv_file(form.csv_file.data, 'Case_Data')
            flash('File uploaded!', 'success')
            return redirect(url_for('home'))

    return render_template('upload_cases.html', title='Upload Cases', form=form)


@app.route('/<variable>/upload_generic', methods=['GET', 'POST'])
@login_required
def upload_generic(variable):
    form = CasesForm()
    if form.validate_on_submit():
        if form.csv_file.data:
            new_file = save_csv_file(form.csv_file.data, variable)
            flash('File uploaded!', 'success')
            return redirect(url_for('home'))

    return render_template('upload_generic.html', title=variable, form=form)


@app.route('/master_space')
@login_required
def master_space():
    return render_template('master_space.html', title='Master Space', username=current_user.username)


@app.route('/verification_of_vacations/<vaca_id>', methods=['GET', 'POST'])
@login_required
def verification_of_vacations(vaca_id):
    cur_vaca = Vacation.query.filter_by(id=vaca_id).first()
    if cur_vaca:
        cur_vaca.is_verified = True
        db.session.commit()
    return 'True'


@app.route('/<judge_id>/master_vacation_view', methods=['GET', 'POST'])
@login_required
def master_vacation_view(judge_id):  # judge_id = judge_id to see vacations of
    # if judge_id == 'none':
    #     judge_id = None
    # vacations = get_all_vacations(judge_id)  # dict -> 'judge_id': vacation.judge_id, 'title': 'חופש' + str(vacation.judge_id), 'start': vacation.start_date, 'end': vacation.end_date
    judges = get_all_relevant_judges()  # dict -> id: judge_id, name: judge_name
    return render_template('master_vacation_view.html', title='Vacations View',
                           judge_id=current_user.id, username=current_user.username, judges=judges)

@app.route('/<judge_id_location>/get_all_judge_events')
@login_required
def get_all_judge_events(judge_id_location):  # judge_id_location = judge_id-location to see events of
    # split judge_id_location to -> judge_id, location
    judge_id, location, hall_number = judge_id_location.split('-')
    if judge_id == 'none':
        judge_id = None
    if hall_number == 'none':
        hall_number = None
    events = get_all_events(judge_id, location, hall_number)  # dict -> 'judge_id': , 'title', 'start': , 'end': , 'id'
    return json.dumps(events)


@app.route('/<location>/get_all_location_judges')
@login_required
def get_all_location_judges(location):
    location = '%' + location + '%'
    judges_objects = Judge.query.filter(Judge.locations.like(location)).all()
    judges = []
    for judge in judges_objects:
        judges.append(
            {
                'id': judge.id,
                'name': judge.username
            }
        )
    return json.dumps(judges)


@app.route('/<location>/get_all_location_halls')
@login_required
def get_all_location_halls(location):
    hall_objects = Hall.query.filter(Hall.location == location).all()
    halls = []
    for hall in hall_objects:
        halls.append(
            {
                'id': hall.hall_number,
                'name': hall.hall_number
            }
        )
    return json.dumps(halls)


@app.route('/judge_case_assignments', methods=['GET', 'POST'])
@login_required
def judge_case_assignments():
    events = get_all_events(judge_id=current_user.id)
    return render_template('judge_case_assignments.html', events=events)


@app.route('/judge_short_vaca', methods=['GET', 'POST'])
@login_required
def judge_short_vaca():
    form = VacaForm()
    events = get_all_events(judge_id=current_user.id)
    if check_date_earlier_than_today(form):
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
        delta = end_date - start_date
        if delta.days <= 3:
            vacation = Vacation(judge_id=current_user.id, is_verified=True, type='Short',
                                   start_date=start_date, end_date=end_date)
            add_to_db(vacation)
            flash('בקשה הוגשה', 'success')
            # finish
            return redirect(url_for('home'))
        else:
            flash('חופשה קצרה יכולה להיות עד 3 ימים, לחופשה ארוכה יותר נע ללכת ל״בקשה לחופשה ארוכה״', 'danger')
    return render_template('judge_short_vaca.html', events=events, form=form)


@app.route('/judge_long_vaca', methods=['GET', 'POST'])
@login_required
def judge_long_vaca():
    form = VacaForm()
    events = get_all_events(judge_id=current_user.id)
    if check_date_earlier_than_today(form):
        if check_not_short_vaca(form):
            start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
            if not check_if_already_vacation(start_date, end_date, current_user.id):
                vacation = Vacation(judge_id=current_user.id, is_verified=False, type='Long',
                                   start_date=start_date, end_date=end_date)
                add_to_db(vacation)
                flash('בקשה הוגשה', 'success')
                # finish
                return redirect(url_for('home'))

    return render_template('judge_long_vaca.html', events=events, form=form)


@app.route('/judge_case_search', methods=['GET', 'POST'])
@login_required
def judge_case_search():
    events = get_all_events(judge_id=current_user.id)
    return render_template('judge_case_search.html', events=events)


@app.route('/judge_personal_space')
@login_required
def judge_personal_space():
    return render_template('judge_personal_space.html', title='Judge Personal Space', username=current_user.username)


@app.route('/secretary_space')
@login_required
def secretary_space():
    return render_template('secretary_space.html', title='Secretary Space')


@app.route('/secretary_upload_files_and_split_cases', methods=['GET', 'POST'])
@login_required
def secretary_upload_files_and_split_cases():
    form = UploadFilesForm()
    colors = get_upload_div_colors()
    if form.validate_on_submit():
        today_date = str(datetime.datetime.now().date())
        files_added = []
        added = False
        secretary_upload_directory = 'Secretary_Upload_Files'
        if form.new_cases_file.data:
            case_csv_file_path = save_csv_file(form.new_cases_file.data, secretary_upload_directory,
                                               'cases_{}.csv'.format(today_date))
            load_cases_to_db(case_csv_file_path)
            files_added.append('תיקים')
            added = True
        if form.holidays_file.data:
            holiday_csv_file = save_csv_file(form.holidays_file.data, secretary_upload_directory,
                                             'holidays_{}.csv'.format(today_date))
            load_holidays_to_db(holiday_csv_file)
            files_added.append('חגים')
            added = True
        if form.rotation_file.data:
            rotation_csv_file = save_csv_file(form.rotation_file.data, secretary_upload_directory,
                                              'rotations_{}.csv'.format(today_date))
            load_rotations_to_db(rotation_csv_file)
            files_added.append('תורנות')
            added = True
        if form.mishmoret_file.data:
            mishmoret_csv_file = save_csv_file(form.mishmoret_file.data, secretary_upload_directory,
                                               'mishmoret_{}.csv'.format(today_date))
            load_mishmoret_to_db(mishmoret_csv_file)
            files_added.append('משמורת')
            added = True

        if added:
            # Flash message
            flash_str = 'קבצים :'
            for filename in files_added:
                flash_str += ' {}'.format(filename)
            flash_str += ' הועלו בהצלחה '
            flash(flash_str, 'success')
        # Run logic
        run_division_logic()
        # Redirect home
        return redirect(url_for('home'))

    return render_template('secretary_upload_files_and_split_cases.html', form=form, colors=colors)


@app.route('/run_logic')
@login_required
def run_logic():
    run_division_logic()
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
            return render_template('home.html')
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
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/initiate_db')
def initiate_db():
    initiator = DBInitiator(db)
    initiator.import_data_to_db()
    flash('Initiated DB', 'info')
    return redirect(url_for('home'))
