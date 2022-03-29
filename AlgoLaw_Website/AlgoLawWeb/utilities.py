from sqlalchemy import or_, and_
from AlgoLawWeb import app, db
from AlgoLawWeb.models import User, Post, ROLES, Vacation
import datetime
import os
from flask import render_template, url_for, flash, redirect, request, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required


###################################### UPLOAD FUNCTIONS #############################################################
def check_available_directory():
    current_year = datetime.datetime.now().year
    current_quarter = (datetime.datetime.now().month - 1 // 3) + 1
    if not os.path.isdir(f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}'):
        os.mkdir(f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}')
    return f'{app.root_path}/Cases_Uploaded/{current_year}_quarter_{current_quarter}'


def save_csv_file(form_csv_file):
    output_dir = check_available_directory()
    uploader_username = current_user.username
    csv_path = os.path.join(app.root_path, output_dir, uploader_username+'_Case_Data.csv')
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


def get_all_vacations(judge_id=None):
    '''
    :param judge_id: if None -> get all vacations of all judges, if ID get vacations of ID judge
    :return: events - dict -> {
        title
        start
        end
        color
    }
    '''
    events = []
    if not judge_id:
        vacations = Vacation.query.all()
        relevant_judges = User.query.all()
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
            event['color'] = '#6495ED'
        else:
            event['color'] = '#DC143C'
        events.append(event)
    return events


###################################### MASTER FUNCTIONS ############################################
def get_all_judges():
    users = User.query.all()
    judges = []
    for user in users:
        if user.role == 'דיין/דיינת':
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

