from flask import render_template, url_for, flash, redirect, send_from_directory, request
from AlgoLawWeb import app, db, bcrypt
from AlgoLawWeb.forms import RegistrationForm, LoginForm, CasesForm, VacaForm, UploadFilesForm, CaseSearchForm, \
    EventForm, lawyerSearchForm, WeightForm
from AlgoLawWeb.models import User, ROLES, Vacation, Judge, Hall, Case, MeetingSchedule, Lawyer
from flask_login import login_user, current_user, logout_user, login_required
import datetime
from AlgoLawWeb.AlgoLawBackEnd import judge_divider
from AlgoLawWeb.utilities import check_if_already_vacation, save_csv_file, \
    get_all_relevant_judges, add_to_db, check_logged_in, \
    return_role_page, insert_output_to_db, get_all_events, load_cases_to_db, load_holidays_to_db, load_rotations_to_db, \
    load_mishmoret_to_db, get_upload_div_colors, get_events_by_role, get_location_by_role, handle_vacation_form, \
    handle_event , find_lawyer, get_case_weights
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


# @app.route('/<variable>/upload_generic', methods=['GET', 'POST'])
# @login_required
# def upload_generic(variable):
#     form = CasesForm()
#     if form.validate_on_submit():
#         if form.csv_file.data:
#             new_file = save_csv_file(form.csv_file.data, variable)
#             flash('File uploaded!', 'success')
#             return redirect(url_for('home'))
#
#     return render_template('upload_generic.html', title=variable, form=form)


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

@app.route('/delete_vacation/<vaca_id>', methods=['GET', 'POST'])
@login_required
def delete_vacation(vaca_id):
    cur_vaca = Vacation.query.filter_by(id=vaca_id).first()
    if cur_vaca:
        db.session.delete(cur_vaca)
        db.session.commit()
    return 'True'



@app.route('/<judge_id>/master_vacation_view', methods=['GET', 'POST'])
@login_required
def master_vacation_view(judge_id):  # judge_id = judge_id to see vacations of
    judges = get_all_relevant_judges()  # dict -> id: judge_id, name: judge_name
    return render_template('master_vacation_view.html', title='Vacations View',
                           judge_id=current_user.id, username=current_user.username, judges=judges)

@app.route('/get_all_judge_events/<judge_id_location>')
@login_required
def get_all_judge_events(judge_id_location):  # judge_id_location = judge_id-location to see events of
    # split judge_id_location to -> judge_id, location, hall_number
    cur_role = ROLES[current_user.role]
    judge_id, location, hall_number, monthly = judge_id_location.split('-')
    if judge_id == 'none':
        judge_id = None
    if hall_number == 'none':
        hall_number = None
    if location == 'none':
        location = None
    if monthly == 'true':
        events = get_events_by_role(cur_role, judge_id=judge_id, monthly=True, hall_number=hall_number, location=location)
    else:
        # events = get_all_events(judge_id, location, hall_number)  # dict -> 'judge_id': , 'title', 'start': , 'end': , 'id'
        events = get_events_by_role(cur_role, judge_id=judge_id, monthly=False, hall_number=hall_number, location=location)
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
            return redirect(url_for('calendar'))
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
        flash(f'נוצר יוזר חדש! נא חכה לאישור יוזר ע״י הנהלה', 'success')
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
            if user.is_validated:
                login_user(user, remember=form.remember.data)
                return redirect(url_for('home'))
            else:
                flash('משתמש עוד לא מאושר, נא לפנות להנהלה', 'danger')
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


@app.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    cur_role = ROLES[current_user.role]
    vacation_form = VacaForm()
    event_from = EventForm()
    if request.form:
        if request.form['submit'] == 'זמן חופשה':
            if vacation_form.start_date.raw_data:
                handle_vacation_form(vacation_form)
        elif request.form['submit'] == 'זמן אירוע':
            if event_from.start_date.raw_data:
                handle_event(event_from)
        redirect(url_for('home'))
    master_view = False
    judge_view = False
    if 'Master' in cur_role:
        master_view = True
    elif cur_role == 'Judge':
        judge_view = True

    return render_template('calendar.html', master_view=master_view, judge_view=judge_view, cur_user_id=current_user.id,
                           vacation_form=vacation_form, event_from=event_from)
@app.route('/secretary_lawyer_search', methods=['GET', 'POST'])
@login_required
def secretary_lawyer_search():
    form = lawyerSearchForm()
    if form.validate_on_submit():
        layers_found = find_lawyer(form.lawyer_name.data , form.lawyer_last_name.data , form.lawyer_id.data, form.lawyer_mail.data,form.lawyer_phone.data)
        return render_template('show_lawyers_search.html', lawyers=layers_found, num_lawyers_found=len(layers_found))
    return render_template('secretary_lawyer_search.html',form=form)

@app.route('/search_cases', methods=['GET', 'POST'])
@login_required
def search_cases():
    form = CaseSearchForm()
    if form.validate_on_submit():
        # Go over all form fields to see which one was used
        if form.orer_id.data:
            orer_search_id = form.orer_id.data
            orer_filter = Case.orer_id.like(orer_search_id)
        else:
            orer_filter = True

        if form.case_id.data:
            case_search_id = form.case_id.data
            case_id_filter = Case.id.like(case_search_id)
        else:
            case_id_filter = True

        if form.lawyer_id.data:
            lawyer_search_id = form.lawyer_id.data
            lawyer_filter = Case.lawyer_id.like(lawyer_search_id)
        else:
            lawyer_filter = True

        if form.main_type.data:
            main_type_search = form.main_type.data
            main_type_filter = Case.first_type.like(main_type_search)
        else:
            main_type_filter = True

        if form.secondary_type.data:
            secondary_type_search = form.secondary_type.data
            secondary_type_filter = Case.second_type.like(secondary_type_search)
        else:
            secondary_type_filter = True

        cases = Case.query.filter(orer_filter,
                                  case_id_filter,
                                  lawyer_filter,
                                  main_type_filter,
                                  secondary_type_filter).all()
        final_cases = []
        for case in cases:
            lawyer_1_id = Lawyer.query.filter(Lawyer.lawyer_id == case.lawyer_id_1).first()
            if lawyer_1_id:
                lawyer_1_id = lawyer_1_id.lawyer_id
            lawyer_2_id = Lawyer.query.filter(Lawyer.lawyer_id == case.lawyer_id_2).first()
            if lawyer_2_id:
                lawyer_2_id = lawyer_2_id.lawyer_id
            schedule = MeetingSchedule.query.join(Hall).\
                            filter(MeetingSchedule.case_id == case.id).\
                            add_column(Hall.hall_number).add_column(Hall.location).\
                            order_by(MeetingSchedule.date.desc()).first()
            if schedule:
                schedule, hall_number, location = schedule
                schedule = location + ', ' + str(hall_number) + ', ' + schedule.start_time + ' - ' + schedule.end_time
                final_cases.append(
                    {
                        'case_id': case.id,
                        'first_type': case.first_type,
                        'second_type': case.second_type,
                        'lawyer_1_id': lawyer_1_id,
                        'lawyer_2_id': lawyer_2_id,
                        'location': schedule
                    }
                )

        return render_template('show_cases_search.html', cases=final_cases, cases_found_num=len(cases))

    return render_template('search_cases.html', form=form)


@app.route('/master_validate_users', methods=['GET', 'POST'])
@login_required
def master_validate_users():
    unvalidated_users = User.query.filter(User.is_validated == False).all()

    return render_template('master_validate_users.html', unvalidated_users=unvalidated_users,
                           num_unvalidated_users=len(unvalidated_users), roles=ROLES.keys())


@app.route('/verify_user/<user_id>/<role>', methods=['GET', 'POST'])
@app.route('/verify_user/<user_id>/<role>/<role2>', methods=['GET', 'POST'])
@app.route('/verify_user/<user_id>/<role>/<role2>/<role3>', methods=['GET', 'POST'])
@app.route('/verify_user/<user_id>/<role>/<role2>/<role3>/<role4>', methods=['GET', 'POST'])
@login_required
def verify_user(user_id, role, role2=None, role3=None, role4=None):
    cur_user = User.query.filter_by(id=user_id).first()
    if cur_user:
        cur_user.is_validated = True
        if role2:
            role = role + '/' + role2
        if role3:
            role = role + '/' + role3
        if role4:
            role = role + '/' + role4

        if cur_user.role != role:
            cur_user.role = role
        db.session.commit()
        flash('משתמש {} אושר במערכת     בתפקיד {} בהצלחה'.format(cur_user.username, cur_user.role), 'success')
    return redirect(url_for('master_validate_users'))


@app.route('/master_change_weights', methods=['GET', 'POST'])
@login_required
def master_change_weights():
    form = WeightForm()
    if form.validate_on_submit():
        # Change weights in DB maybe I dunno
        pass

    weights = get_case_weights(datetime.datetime.now().year)
    return render_template('master_change_weights.html', weights=weights, form=form)
