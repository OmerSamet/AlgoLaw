from sqlalchemy import or_, and_
from AlgoLawWeb import app, db
from AlgoLawWeb.models import User, ROLES, Vacation, CaseJudgeLocation, Case, MeetingSchedule, Judge, Hall, Lawyer
import datetime
import os
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
from collections import defaultdict


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


def save_csv_file(form_csv_file, variable):
    output_dir = check_available_directory()
    uploader_username = current_user.username
    csv_path = os.path.join(app.root_path, output_dir, uploader_username, '_', variable, '.csv')
    form_csv_file.save(csv_path)
    return csv_path


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


################################################## LAWYERS STUF ###########################################################

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
            'last name': found.last_name,
             'id': found.lawyer_id,
             'mail': found.mail,
             'phone number':found.phone_number
         }
         lawyers.append(lawyer)
    return lawyers