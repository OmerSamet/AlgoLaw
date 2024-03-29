from sqlalchemy import or_, and_

from AlgoLaw_Website.AlgoLawWeb import app, db
from AlgoLaw_Website.AlgoLawWeb.AlgoLawBackEnd.config import CaseWeightDir
from AlgoLaw_Website.AlgoLawWeb.models import User, Judge, ROLES, Vacation, CaseJudgeLocation, Case, MeetingSchedule, Judge, Hall, \
    Rotation, Event, Lawyer
import datetime
import os
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
from collections import defaultdict
import time


#  {daynum: {hall_number: [judge1, judge2]
DayToHallToJudgeJerusalem = {
    7: {1: [1, 1], 2: [2, 2], 3: [9, 10]},  # Sunday
    1: {1: [3, 3], 2: [4, 4], 3: [7, 8]},  # Monday
    2: {1: [5, 5], 2: [6, 6], 3: [0, 2]},  # Tuesday
    3: {1: [7, 7], 2: [8, 8], 3: [3, 4]},  # Wednesday
    4: {1: [9, 9], 2: [10, 10], 3: [5, 6]}  # Thursday
}
DayToHallToJudgeTelAviv = {
    7: {1: [9, 9], 2: [10, 10]},  # Sunday
    1: {1: [9, 9], 2: [10, 10]},  # Monday
    2: {1: [9, 9], 2: [10, 10]},  # Tuesday
    3: {1: [9, 9], 2: [10, 10]},  # Wednesday
    4: {1: [9, 9], 2: [10, 10]}  # Thursday
}

DayToHallToJudgeHeifa = {
    7: {1: [1, 1]},  # Sunday
    1: {1: [1, 1]},  # Monday
    2: {1: [1, 1]},  # Tuesday
    3: {1: [1, 1]},  # Wednesday
    4: {1: [1, 1]}  # Thursday
}
DayToHallToJudgeBeerSheva = {
    7: {1: [4, 4]},  # Sunday
    1: {1: [4, 4]},  # Monday
    2: {1: [4, 4]},  # Tuesday
    3: {1: [4, 4]},  # Wednesday
    4: {1: [4, 4]}# Thursday
}
LocationEngToHeb = {
    'Jerusalem': 'ירושלים',
    'Haifa': 'חיפה',
    'Beer Sheva': 'באר שבע',
    'Tel Aviv': 'תל אביב'
}

HALL_NUMBER_TO_BORDER_COLOR = {
    1: '#8A2BE2',
    2: '#1E90FF',
    3: '#20B2AA'
}

EVENT_COLORS = {
    'VACATION_VERIFIED': '#3CB371',
    'VACATION_UNVERIFIED': '#DC143C',
    'CASE_CONFIRMED': '#6495ED',
    'CASE_NOT_CONFIRMED': '#8B0000',
    'MONTHLY_EVENT': '#7B68EE'
}

ROLES_EN_TO_HE = {
    'Judge': 'דיין/דיינת',
    'Secretary': 'מזכיר/מזכירה',
    'Master': 'הנהלה'
}


###################################### UPLOAD FUNCTIONS #############################################################
def load_files_from_form(form):
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

    return added, files_added


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


def get_case_db_data(case_enrichment_df, main_type):
    pandas_query = (case_enrichment_df['Main_Type'] == main_type)

    try:
        c_urg_level = case_enrichment_df[pandas_query]['Urgency_Level'].values[0]
        c_duration = 35
        c_weight = int.from_bytes(case_enrichment_df[pandas_query]['Weight'].values[0], 'little')
    except Exception as e:
        print('got here!')
        print(main_type)

    return c_urg_level, c_duration, c_weight

# def get_case_db_data(case_enrichment_df, main_type, second_type, sub_type):
#         if type(sub_type) == str:
#             pandas_query = (case_enrichment_df['Main_Type'] == main_type) & (
#                     case_enrichment_df['Secondary_Type'] == second_type) & (
#                                    case_enrichment_df['Sub_Type'] == sub_type)
#         else:
#             pandas_query = (case_enrichment_df['Main_Type'] == main_type) & (
#                     case_enrichment_df['Secondary_Type'] == second_type)
#
#         c_urg_level = case_enrichment_df[pandas_query]['Urgency_Level'].values[0]
#         c_duration = 35
#         c_weight = int.from_bytes(case_enrichment_df[pandas_query]['Weight'].values[0], 'little')
#
#         return c_urg_level, c_duration, c_weight


def read_excel_file(file_path):
    try:
        df = pd.read_csv(file_path).fillna('NO DATA')
    except Exception as e:
        df = pd.read_excel(file_path).fillna('NO DATA')
    return df


def load_cases_to_db(case_file_path):
    case_enrichment_data_path = os.path.join(app.root_path, 'DB_DATA', 'Case_Data.csv')

    case_enrichment_df = pd.read_csv(case_enrichment_data_path).fillna('NO DATA')
    cases_df = read_excel_file(case_file_path)
    for index, row in cases_df.iterrows():
        case_id = row['מספר תיק']
        main_type = row['נושא עיקרי']
        second_type = ''
        sub_type = ''
        # main_type = row['Case_Main_Type']
        # second_type = row['Secondary_Type']
        # sub_type = row['Case_sub_type']
        # location = row['Location']
        location = row['שם בית דין']
        location = location.replace('בית דין ', '')
        lawyer_name = row['שם ב"כ העורר']
        lawyer_id_2 = ''
        # lawyer_id_1 = row['Lawyer_ID_1']
        # lawyer_id_2 = row['Lawyer_ID_2']

        urg_level, duration, weight = get_case_db_data(case_enrichment_df, main_type)
        # urg_level, duration, weight = get_case_db_data(case_enrichment_df, main_type,
        #                                                second_type, sub_type)
        case_sanity_check = db.session.query(Case).filter(Case.id==case_id).all()
        if (len(case_sanity_check) == 0):
            new_case = Case(id=case_id,
                            first_type=main_type,
                            second_type=second_type,
                            third_type=sub_type,
                            urgency_level=urg_level,
                            duration=duration,
                            location=location,
                            weight=weight,
                            quarter_created=((datetime.datetime.now().month - 1) // 3) + 1,
                            year_created=datetime.datetime.now().year,
                            lawyer_id_1=lawyer_name,
                            lawyer_id_2=lawyer_id_2)

            add_to_db(new_case)
    return True


def load_holidays_to_db(holiday_csv_file):
    holidays_df = read_excel_file(holiday_csv_file)

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
    rotation_df = read_excel_file(rotation_csv_file)
    for index, row in rotation_df.iterrows():
        rotation = Rotation(judge_id=row['Judge_ID'],
                            start_date=datetime.datetime.strptime(row['Start_Date'], '%d/%m/%Y'),
                            end_date=datetime.datetime.strptime(row['End_Date'], '%d/%m/%Y'))
        add_to_db(rotation)

    return True


def load_mishmoret_to_db(mishmoret_csv_file):
    mishmoret_df = pd.read_csv(mishmoret_csv_file)

    for index, row in mishmoret_df.iterrows():
        start_date = datetime.datetime.strptime(row['Start_Date'], '%d/%m/%Y')
        end_date = datetime.datetime.strptime(row['End_Date'], '%d/%m/%Y')
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


def get_upload_div_colors_and_dates():
    colors = {'cases': '#FFE4B5',
              'holidays': '#FFE4B5',
              'rotations': '#FFE4B5',
              'mishmoret': '#FFE4B5'}
    upload_dates = {'cases': '',
                    'holidays': '',
                    'rotations': '',
                    'mishmoret': ''}
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
        upload_dates[event_type] = str(latest_date.date())
        if latest_date > datetime.datetime.now()-datetime.timedelta(days=30):
            colors[event_type] = '#87CEFA'

    return colors, upload_dates


###################################### CALENDAR FUNCTIONS ############################################
def check_event_is_same_day(start_date, end_date):
    return start_date.date() == end_date.date()


def handle_event(form):
    if check_date_earlier_than_today(form):
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%dT%H:%M:%S%z')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%dT%H:%M:%S%z')
        if check_event_is_same_day(start_date, end_date):
            event = Event(judge_id=current_user.id, start_date=start_date, end_date=end_date)
            add_to_db(event)
            flash('נוצר אירוע', 'success')
            pass
        pass


def handle_vacation_form(form):
    if check_date_earlier_than_today(form):
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
        if not check_if_already_vacation(start_date, end_date, current_user.id):
            if check_if_short_vaca(form):
                # Got short Vacation
                vacation = Vacation(judge_id=current_user.id, is_verified=True, type='Short',
                                                   start_date=start_date, end_date=end_date)
                add_to_db(vacation)
                flash('בקשה לחופשה קצרה הוגשה', 'success')
            else:
                # Got long vacation
                vacation = Vacation(judge_id=current_user.id, is_verified=False, type='Long',
                                                   start_date=start_date, end_date=end_date)
                add_to_db(vacation)
                flash('בקשה לחופשה ארוכה הוגשה', 'success')


def check_date_earlier_than_today(form):
    if form.start_date.raw_data is not None:
        try:
            start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        except:
            start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
        if start_date <= datetime.datetime.today():
            flash('תאריך צריך להיות לפחות היום או מאוחר יותר', 'danger')
            return False
    else:
        return False
    return True


def get_location_by_role(cur_role, current_user_id):
    if 'Master' in cur_role:
        return 'Jerusalem'
    elif 'Secretary' in cur_role:
        location = cur_role.split(' ')
        location = location.pop()
        if len(location) > 1:
            location = ' '.join(location)
            return location
        else:
            return location[0]
    else:
        #Judge
        location = Judge.query.filter(Judge.user_id == current_user_id).first()
        if ',' in location:
            return 'All'
        else:
            return location

def role_to_location(role):
    if 'Master' in role:
        return None  # to get all locations
    elif 'Jerusalem' in role:
        return 'Jerusalem'
    elif 'Haifa' in role:
        return 'Haifa'
    elif 'Tel Aviv' in role:
        return 'Tel Aviv'
    elif 'Beer Sheva' in role:
        return 'Beer Sheva'


def get_events_by_role(role, judge_id=None, monthly=False, location=None, hall_number=None):
    if role == 'Judge':
        events = get_all_events(judge_id=judge_id, location=location, hall_number=hall_number)
    else:
        if not location:
            location = role_to_location(role)
        events = get_all_events(judge_id=judge_id, location=location, hall_number=hall_number)

    if monthly:
        events = turn_events_to_monthly(events)
    return events


def turn_events_to_monthly(events):
    daily_events = []
    date_to_hall_number_to_judge = defaultdict(lambda: defaultdict(set))
    for event in events:
        if event['type'] == 'meeting':
            event_date = str(datetime.datetime.strptime(event['start'], '%Y-%m-%d %H:%M:%S').date())
            event_hall_number = event['hall_id']
            judge_id = event['judge_id']  # ID in Judge table

            date_to_hall_number_to_judge[event_date][event_hall_number].add(judge_id)
        else:
            daily_events.append(event)

    for event_date, hall_number_dict in date_to_hall_number_to_judge.items():
        # date_title = ''
        for hall_number, judge_ids in hall_number_dict.items():
            for judge_id in judge_ids:
                judge_name = Judge.query.filter(Judge.id == judge_id).first().username
                # date_title = judge_name + ' ' + str(hall_number) + ' - אולם'
                date_title = 'אולם ' + str(hall_number) + ' - ' + judge_name
                start = '09:00'
                end = '14:50'
                event_date_obj = datetime.datetime.strptime(event_date, '%Y-%m-%d')
                event_start_time = datetime.datetime.strptime(start, '%H:%M').time()
                event_start_time = datetime.datetime.combine(event_date_obj, event_start_time)
                event_end_time = datetime.datetime.strptime(end, '%H:%M').time()
                event_end_time = datetime.datetime.combine(event_date_obj, event_end_time)
                daily_event = {
                    'title': date_title,
                    'start': str(event_start_time),
                    'end': str(event_end_time),
                    'color': EVENT_COLORS['MONTHLY_EVENT'],
                    'display': 'block',
                    'is_verified': True,
                    'allDay': True
                }
                daily_events.append(daily_event)

    return daily_events

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


def check_if_short_vaca(form):
    if form.start_date.raw_data is not None:
        start_date = datetime.datetime.strptime(form.start_date.raw_data[0], '%Y-%m-%d')
        end_date = datetime.datetime.strptime(form.end_date.raw_data[0], '%Y-%m-%d')
        delta = end_date - start_date
        if delta.days <= 3:
            return True

    return False


def get_case_id_to_title(case_id_judge_id):
    case_id_to_title = defaultdict(str)
    for case_id, judge_id, lawyer_id_1, lawyer_id_2 in case_id_judge_id:
        case = Case.query.filter(Case.id == case_id).first()
        judge = Judge.query.filter(Judge.id == judge_id).first()
        meeting = MeetingSchedule.query.filter(MeetingSchedule.case_id == case.id).first()
        hall_num = hall_id_to_hall_num(meeting.hall_id)
        # lawyer_2 = Lawyer.query.filter(Lawyer.lawyer_id == lawyer_id_2).first()
        # lawyer_1 = Lawyer.query.filter(Lawyer.lawyer_id == lawyer_id_1).first()
        case_id_to_title[case.id] = judge.username + ' - ' + case.first_type + ' - אולם ' + str(hall_num)

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


def hall_id_to_hall_num(hall_id):
    return Hall.query.filter(Hall.id == hall_id).first().hall_number


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

    else:
        meetings = MeetingSchedule.query.join(Hall).filter(MeetingSchedule.judge_id == judge_id,
                                                           Hall.location.like(location),
                                                           Hall.hall_number.like(hall_number)).all()

    case_id_to_title = get_case_id_to_title([(meeting.case_id, meeting.judge_id, meeting.lawyer_id_1, meeting.lawyer_id_2) for meeting in meetings])
    for meeting in meetings:
        case_start_time = datetime.datetime.strptime(meeting.start_time, '%H:%M').time()
        case_end_time = datetime.datetime.strptime(meeting.end_time, '%H:%M').time()
        case_start_date = datetime.datetime.combine(meeting.date, case_start_time)
        case_end_date = datetime.datetime.combine(meeting.date, case_end_time)
        hall_num = hall_id_to_hall_num(meeting.hall_id)
        event = {
            'judge_id': meeting.judge_id,
            'title': case_id_to_title[meeting.case_id],
            'start': str(case_start_date),
            'end': str(case_end_date),
            'id': meeting.id,
            'is_verified': meeting.is_verified,
            'type': 'meeting',
            'hall_id': hall_num,
            'display': 'block',
            'allDay': False,
            'BackgroudColor': HALL_NUMBER_TO_BORDER_COLOR[hall_num]
        }
        if meeting.is_verified:
            # event['color'] = EVENT_COLORS['CASE_CONFIRMED']
            event['color'] = HALL_NUMBER_TO_BORDER_COLOR[hall_num]
        else:
            # event['color'] = EVENT_COLORS['CASE_NOT_CONFIRMED']
            event['color'] = HALL_NUMBER_TO_BORDER_COLOR[hall_num]
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
        if vacation.type in ('Short', 'Long'):
            title = 'חופש ' + judges_dict[vacation.judge_id]
            judge_id = vacation.judge_id
            vaca_id = vacation.id
        elif vacation.type == 'Mishmoret':
            title = 'משמורת ' + judges_dict[vacation.judge_id]
            judge_id = vacation.judge_id
            vaca_id = vacation.id
        else:
            title = vacation.type
            judge_id = 'All'
            vaca_id = 0
        event = {
            'judge_id': judge_id,
            'title': title,
            'start': str(vacation.start_date),
            'end': str(vacation.end_date),
            'id': vaca_id,
            'is_verified': vacation.is_verified,
            'type': 'vacation',
            'display': 'block',
            'allDay': True
        }
        if vacation.type == 'Mishmoret':
            event['color'] = '#66CDAA'
            event['BackgroudColor'] = '#66CDAA'
        elif vacation.is_verified:
            event['color'] = EVENT_COLORS['VACATION_VERIFIED']
            event['BackgroudColor'] = EVENT_COLORS['VACATION_VERIFIED']
        else:
            event['color'] = EVENT_COLORS['VACATION_UNVERIFIED']
            event['BackgroudColor'] = EVENT_COLORS['VACATION_VERIFIED']

        if event not in events:
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


# def get_summon_data_from_db(case_id):
#     meetings = MeetingSchedule.query.filter(MeetingSchedule.case_id == case_id).all()
#     cases
#     for meeting in meetings:
#         title
#         description
#         start_time = str(meeting.date).split(' ')[0] + 'T' + meeting.end_time + ':00-' + meeting.start_time. + ':00'
#         end_time = str(meeting.date).split(' ')[0] + 'T' + meeting.end_time + ':00-' + meeting.start_time. + ':00'
#         attendees_mails
#         location
#
#         title = 'TestTESTTest'
#         description = 'This is my test description'
#         attendees_mails = ['mailomersamet@gmail.com', 'xxhe4433@gmail.com']
#         location = 'Jerusalem, Hall 1'


###################################### MASTER FUNCTIONS ############################################
def get_all_relevant_judges(location='Jerusalem'):
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
    elif 'Secretary' in cur_role:
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


################################################## LAWYERS STUFF ###########################################################

def insert_new_lawyer(name , last_name , lawyer_id, mail,phone_number):
    lawyer = Lawyer(name=name ,
                    last_name=last_name
                    ,lawyer_id=lawyer_id
                    ,mail=mail,
                    phone_number=phone_number)
    add_to_db(lawyer)



def find_lawyer(name , last_name , lawyer_id, mail,phone_number):
    #checking the input and selecting thr right filters to work with
    if name != '':
        name_filter = Lawyer.name.like(name)
    else:
        name_filter = True
    if last_name != '':
        last_name_filter = Lawyer.last_name.like(last_name)
    else:
        last_name_filter = True
    if lawyer_id != '':
        lawyer_id_filter = Lawyer.lawyer_id.like(lawyer_id)
    else:
        lawyer_id_filter = True
    if mail != '':
        mail_filter = Lawyer.mail.like(mail)
    else:
        mail_filter = True
    if phone_number != '':
        phone_number_filter = Lawyer.phone_number.like(phone_number)
    else:
        phone_number_filter = True
    found_lawyers = Lawyer.query.filter(name_filter,last_name_filter,lawyer_id_filter,mail_filter,phone_number_filter).all()
    lawyers = []
    for found in found_lawyers:
         lawyer = {
            'name': found.name,
            'last_name': found.last_name,
             'id': found.lawyer_id,
             'mail': found.mail,
             'phone_number':found.phone_number
         }
         lawyers.append(lawyer)
    return lawyers


def get_case_weights(year='2020'):
    weights = defaultdict(str)
    weight_df = pd.read_excel(CaseWeightDir)
    for index, row in weight_df.iterrows():
        weights[row['Type']] = row[year]

    return weights
