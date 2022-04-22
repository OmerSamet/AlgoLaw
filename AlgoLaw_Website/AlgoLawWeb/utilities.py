from sqlalchemy import or_, and_

from AlgoLawBackEnd import judge_divider
from AlgoLawWeb import app, db
from AlgoLawWeb.models import User, Judge, ROLES, Vacation, CaseJudgeLocation, Case, MeetingSchedule, Judge, Hall, \
    Rotation
import datetime
import os
from flask import flash, redirect, request, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
from collections import defaultdict
import time


EVENT_COLORS = {
    'VACATION_VERIFIED': '#3CB371',
    'VACATION_UNVERIFIED': '#DC143C',
    'CASE_CONFIRMED': '#6495ED',
    'CASE_NOT_CONFIRMED': '#8B0000'
}

ROLES_EN_TO_HE = {
    'Judge': 'דיין/דיינת',
    'Secretary': 'מזכיר/מזכירה',
    'Master': 'הנהלה'
}


###################################### UPLOAD FUNCTIONS #############################################################
def check_available_directory():
    current_year = datetime.datetime.now().year
    current_quarter = (datetime.datetime.now().month - 1 // 3) + 1
    if not os.path.isdir(f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}'):
        os.mkdir(f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}')
    return f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}'


def save_csv_file(form_csv_file, output_directory, file_name):
    csv_path = os.path.join(app.root_path, output_directory, file_name)
    form_csv_file.save(csv_path)
    return csv_path


def get_case_db_data(case_enrichment_df, main_type, second_type, sub_type):
        if type(sub_type) == str:
            pandas_query = (case_enrichment_df['Main_Type'] == main_type) & (
                    case_enrichment_df['Secondary_Type'] == second_type) & (
                                   case_enrichment_df['Sub_Type'] == sub_type)
        else:
            pandas_query = (case_enrichment_df['Main_Type'] == main_type) & (
                    case_enrichment_df['Secondary_Type'] == second_type)

        c_urg_level = case_enrichment_df[pandas_query]['Urgency_Level'].values[0]
        c_duration = 35
        c_weight = case_enrichment_df[pandas_query]['Weight'].values[0]

        return c_urg_level, c_duration, c_weight


def load_cases_to_db(case_file_path):
    case_enrichment_data_path = os.path.join(app.root_path, 'DB_DATA', 'Case_Data.csv')

    case_enrichment_df = pd.read_csv(case_enrichment_data_path).fillna('NO DATA')
    cases_df = pd.read_csv(case_file_path).fillna('NO DATA')
    for index, row in cases_df.iterrows():
        main_type = row['Case_Main_Type']
        second_type = row['Secondary_Type']
        sub_type = row['Case_sub_type']
        location = row['Location']

        urg_level, duration, weight = get_case_db_data(case_enrichment_df, main_type,
                                                       second_type, sub_type)

        new_case = Case(first_type=main_type,
                        second_type=second_type,
                        third_type=sub_type,
                        urgency_level=urg_level,
                        duration=duration,
                        location=location,
                        weight=weight,
                        quarter_created=((datetime.datetime.now().month - 1) // 3) + 1,
                        year_created=datetime.datetime.now().year)

        add_to_db(new_case)

    return True


def load_holidays_to_db(holiday_csv_file):
    holidays_df = pd.read_csv(holiday_csv_file)

    all_judges = Judge.query.all()
    all_judge_ids = [judge.user_id for judge in all_judges]

    for index, row in holidays_df.iterrows():

        start_date = datetime.datetime.strptime(row['Start_Date'], '%d/%m/%Y')
        end_date = datetime.datetime.strptime(row['End_Date'], '%d/%m/%Y')
        name = row['Holiday']
        for judge_id in all_judge_ids:
            vacation = Vacation(judge_id=judge_id,
                                start_date=start_date,
                                end_date=end_date,
                                is_verified=True,
                                type=name)
            add_to_db(vacation)


def load_rotations_to_db(rotation_csv_file):
    rotation_df = pd.read_csv(rotation_csv_file)
    for index, row in rotation_df.iterrows():
        rotation = Rotation(judge_id=row['Judge_ID'],
                            start_date=datetime.datetime.strptime(row['Start_Date'], '%Y-%m-%d'),
                            end_date=datetime.datetime.strptime(row['End_Date'], '%Y-%m-%d'))
        add_to_db(rotation)

    return True


def load_mishmoret_to_db(mishmoret_csv_file):
    mishmoret_df = pd.read_csv(mishmoret_csv_file)

    for index, row in mishmoret_df.iterrrows():
        start_date = row['Start_Date']
        end_date = row['End_Date']
        judge_id = row['Judge_ID']
        vacation = Vacation(judge_id=judge_id,
                            start_date=start_date,
                            end_date=end_date,
                            is_verified=True,
                            type='Mishmoret')
        add_to_db(vacation)


def check_later_date(file_path, latest_date):
    file_date = time.ctime(os.path.getmtime(file_path))
    file_date = datetime.datetime.strptime(file_date, "%a %b %d %H:%M:%S %Y")
    if file_date > latest_date:
        return file_date
    else:
        return latest_date


def get_upload_div_colors():
    colors = {'cases': '#FFE4B5',
              'holidays': '#FFE4B5',
              'rotations': '#FFE4B5',
              'mishmoret': '#FFE4B5'}
    file_names = os.listdir(os.path.join(app.root_path, 'Secretary_Upload_Files'))
    most_recent_dates = {
        'cases': datetime.datetime.now()-datetime.timedelta(days=1000),
        'holidays': datetime.datetime.now()-datetime.timedelta(days=1000),
        'rotations': datetime.datetime.now()-datetime.timedelta(days=1000),
        'mishmoret': datetime.datetime.now()-datetime.timedelta(days=1000)
        }
    for file_name in file_names:
        file_path = os.path.join(app.root_path, 'Secretary_Upload_Files', file_name)
        if os.path.isfile(file_path):
            if 'cases' in file_path:
                most_recent_dates['cases'] = check_later_date(file_path, most_recent_dates['cases'])
            elif 'holidays' in file_path:
                most_recent_dates['holidays'] = check_later_date(file_path, most_recent_dates['holidays'])
            elif 'rotations' in file_path:
                most_recent_dates['rotations'] = check_later_date(file_path, most_recent_dates['rotations'])
            elif 'mishmoret' in file_path:
                most_recent_dates['mishmoret'] = check_later_date(file_path, most_recent_dates['mishmoret'])

    for event_type, latest_date in most_recent_dates.items():
        if latest_date > datetime.datetime.now()-datetime.timedelta(days=30):
            colors[event_type] = '#87CEFA'

    return colors


###################################### CALENDAR FUNCTIONS ############################################
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


###################################### VACATION FUNCTIONS #############################################################
def check_if_already_vacation(start_date, end_date, judge_id):
    overlapping_vacations = db.session.query(Vacation).filter(Vacation.judge_id == judge_id,
                                                                 or_(
                                                                     # new vacation inside old vacation
                                                                     and_(start_date >= Vacation.start_date,
                                                                          end_date <= Vacation.end_date),
                                                                     # new vacation starts before old vacation but ends during old vacation
                                                                     and_(start_date < Vacation.start_date,
                                                                          end_date >= Vacation.start_date,
                                                                          end_date <= Vacation.end_date),
                                                                     # new vacation starts after old vacations starts but before old one ends
                                                                     and_(start_date >= Vacation.start_date,
                                                                          start_date <= Vacation.end_date,
                                                                          end_date > Vacation.end_date)
                                                                    )
                                                                 ).all()
    if overlapping_vacations:
        flash('קיימת כבר חופשה על התאריכים האלה', 'warning')
        return True
    return False


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


def get_case_id_to_title(case_id_judge_id):
    case_id_to_title = defaultdict(str)
    for case_id, judge_id in case_id_judge_id:
        case = Case.query.filter(Case.id == case_id).first()
        judge = Judge.query.filter(Judge.id == judge_id).first()
        case_id_to_title[case.id] = judge.username + ' - ' + case.first_type

    return case_id_to_title


def get_judge_user_ids(location):
    relevant_users = User.query.filter(User.role == ROLES_EN_TO_HE['Judge']).all()
    relevant_user_judges_ids = [user.id for user in relevant_users]
    relevant_judges = Judge.query.filter(Judge.user_id.in_(relevant_user_judges_ids),
                                         Judge.locations.like(location)).all()
    relevant_judges_ids = [judge.user_id for judge in relevant_judges]
    return relevant_judges_ids, relevant_judges


def check_location_and_hall_number(location):
    if location is None:
        return '%'
    return '%' + location + '%'


def get_all_meetings(judge_id=None, location=None, hall_number=None):
    '''
        :param judge_id: if None -> get all cases of all judges, if ID get cases of ID judge
        :param location: get meetings of people from this location
        :return: events - dict -> {
            judge_id
            title
            start
            end
            id
            color
        }
    '''
    location = check_location_and_hall_number(location)
    hall_number = check_location_and_hall_number(hall_number)
    events = []
    if not judge_id:
        relevant_judges_ids, relevant_judges = get_judge_user_ids(location)
        meetings = MeetingSchedule.query.join(Hall).filter(MeetingSchedule.judge_id.in_(relevant_judges_ids),
                                                           Hall.location.like(location),
                                                           Hall.hall_number.like(hall_number)).all()
        # userList = users.query.join(friendships)
        #                   .add_columns(users.id, users.userName, users.userEmail, friendships.user_id, friendships.friend_id).
        #                   filter(users.id == friendships.friend_id).
        #                   filter(friendships.user_id == userID).paginate(page, 1, False)

    else:
        meetings = MeetingSchedule.query.join(Hall).filter(MeetingSchedule.judge_id == judge_id,
                                                           Hall.location.like(location),
                                                           Hall.hall_number.like(hall_number)).all()

    case_id_to_title = get_case_id_to_title([(meeting.case_id, meeting.judge_id) for meeting in meetings])
    for meeting in meetings:
        case_start_time = datetime.datetime.strptime(meeting.start_time, '%H:%M').time()
        case_end_time = datetime.datetime.strptime(meeting.end_time, '%H:%M').time()
        case_start_date = datetime.datetime.combine(meeting.date, case_start_time)
        case_end_date = datetime.datetime.combine(meeting.date, case_end_time)
        event = {
            'judge_id': meeting.judge_id,
            'title': case_id_to_title[meeting.case_id],
            'start': str(case_start_date),
            'end': str(case_end_date),
            'id': meeting.id
        }
        if meeting.is_verified:
            event['color'] = EVENT_COLORS['CASE_CONFIRMED']
        else:
            event['color'] = EVENT_COLORS['CASE_NOT_CONFIRMED']
        events.append(event)
    return events


def get_all_vacations(judge_id=None, location=None):
    '''
    :param judge_id: if None -> get all vacations of all judges, if ID get vacations of ID judge
    :param location: get vacations of people from this location
    :return: events - dict -> {
        judge_id
        title
        start
        end
        id
        color
    }
    '''
    location = check_location_and_hall_number(location)
    events = []
    if not judge_id:
        relevant_judges_ids, relevant_judges = get_judge_user_ids(location)
        vacations = Vacation.query.filter(Vacation.judge_id.in_(relevant_judges_ids)).all()
    else:
        vacations = Vacation.query.filter_by(judge_id=judge_id).all()
        relevant_judges = User.query.filter_by(id=judge_id).all()

    judges_dict = {judge.id: judge.username for judge in relevant_judges}
    for vacation in vacations:
        event = {
            'judge_id': vacation.judge_id,
            'title': 'חופש ' + judges_dict[vacation.judge_id],
            'start': str(vacation.start_date),
            'end': str(vacation.end_date),
            'id': vacation.id
        }
        if vacation.is_verified:
            event['color'] = EVENT_COLORS['VACATION_VERIFIED']
        else:
            event['color'] = EVENT_COLORS['VACATION_UNVERIFIED']
        events.append(event)
    return events


def get_all_events(judge_id=None, location=None, hall_number=None):
    '''
    :param judge_id: judge_id to get events of
    :param location: location of events
    :return:
    '''
    events = []
    vacations = get_all_vacations(judge_id=judge_id, location=location)
    events.extend(vacations)
    meetings = get_all_meetings(judge_id=judge_id, location=location, hall_number=hall_number)
    events.extend(meetings)

    return events

###################################### MASTER FUNCTIONS ############################################
def get_all_relevant_judges(location='Jerusalem'):
    # relevant_user_ids = get_judge_user_ids(location)
    # location = '%' + location + '%'
    location_judges = Judge.query.filter(Judge.locations.like(location)).all()
    judges = []
    for user in location_judges:
        judge = {
            'id': user.id,
            'name': user.username
        }
        judges.append(judge)
    return judges


###################################### SECRATARY FUNCTIONS ############################################
def get_upload_button_colors():
    #os.path.getmtime()
    #os.path.getctime()
    #os.path.join(app.root_path, 'DB_DATA', 'Judge_Data.csv')
    pass

###################################### LOGIN / LOGOUT FUNCTIONS #####################################################
def return_role_page(cur_role):
    if cur_role == 'Master':
        return 1
    elif cur_role == 'Judge':
        return 2
    elif cur_role == 'Secretary':
        return 3
    else:
        return 4


###################################### UTILITY FUNCTIONS #############################################################
def check_logged_in():
    if current_user.is_authenticated:
        return True
    else:
        return False


def add_to_db(data_to_add):
    db.session.add(data_to_add)
    db.session.commit()


def insert_output_to_db(output_path):
    data = pd.read_csv(output_path)
    for index, row in data.iterrows():
        case_id = row['ID Case']
        judge_id = row['ID judge']
        location = row['Location']
        quarter = ((datetime.datetime.now().month-1) // 3) + 1
        year = datetime.datetime.now().year
        case_judge_location = CaseJudgeLocation(case_id=case_id,
                                                judge_id=judge_id,
                                                location=location,
                                                quarter=quarter,
                                                year=year)
        add_to_db(case_judge_location)
