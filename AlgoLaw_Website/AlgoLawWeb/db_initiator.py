import pandas as pd
from AlgoLaw_Website.AlgoLawWeb import db, login_manager, bcrypt
from AlgoLaw_Website.AlgoLawWeb.models import User, Post, ROLES, Vacation, Judge, Hall, Rotation, Case,Lawyer
from AlgoLaw_Website.AlgoLawWeb.utilities import add_to_db
import datetime
from AlgoLaw_Website.AlgoLawWeb import app
import os


class DBInitiator:
    def __init__(self, db):
        self.db = db
        self.case_enrichment_data_path = os.path.join(app.root_path, 'DB_DATA', 'Case_Data.csv')
        self.fake_cases_csv_path = os.path.join(app.root_path, 'DB_DATA', 'Fake_case_data.csv')
        self.judge_data_csv_path = os.path.join(app.root_path, 'DB_DATA', 'Judge_Data.csv')
        self.halls_data_csv_path = os.path.join(app.root_path, 'DB_DATA', 'Halls.csv')
        self.rotation_data_csv_path = os.path.join(app.root_path, 'DB_DATA', 'Judge_Rotation_Schedule.csv')
        self.lawyers_csv_path = os.path.join(app.root_path, 'DB_DATA','Lawyers.csv')

    def import_data_to_db(self):
        # Delete current DB and create empty DB
        self.db.drop_all()
        self.db.create_all()

        # Get all data to DataFrames
        judges = self.add_judges_to_db()
        halls = self.add_halls_to_db()
        rotation_dates = self.add_rotation_dates_to_db()
        # cases = self.add_cases_to_db()
        cases = 1
        self.add_lawyers_to_db()

        self.check_csv_imports(cases, judges, halls, rotation_dates)

        users, vacations = self.add_users_and_vacations_to_site()
        print(f'Added {len(users)} users and {len(vacations)} vacations')

    @staticmethod
    def add_users_and_vacations_to_site():
        user1 = User(username="TestJudge",
                     email="TestJudge@justice.com",
                     password=bcrypt.generate_password_hash("TestJudge123!@#").decode('utf-8'),
                     role="דיין/דיינת",
                     is_validated=True)
        user2 = User(username="TestSecretarMaster",
                     email="TestSecretary@justice.com",
                     password=bcrypt.generate_password_hash("TestSecretary123!@#").decode('utf-8'),
                     role="מזכיר/ה ראשי/ת",
                     is_validated=True)
        user3 = User(username="TestMaster",
                     email="TestMaster@justice.com",
                     password=bcrypt.generate_password_hash("TestMaster123!@#").decode('utf-8'),
                     role="הנהלה",
                     is_validated=True)
        user4 = User(username="TestSecretaryJersulam",
                     email="TestSecretaryJ@justice.com",
                     password=bcrypt.generate_password_hash("TestSecretary123!@#").decode('utf-8'),
                     role="מזכיר/ה מחוז ירושלים",
                     is_validated=True)
        user5 = User(username="TestSecretarHaifa",
                     email="TestSecretaryH@justice.com",
                     password=bcrypt.generate_password_hash("TestSecretary123!@#").decode('utf-8'),
                     role="מזכיר/ה מחוז חיפה",
                     is_validated=True)
        user6 = User(username="TestSecretarTelAviv",
                     email="TestSecretaryT@justice.com",
                     password=bcrypt.generate_password_hash("TestSecretary123!@#").decode('utf-8'),
                     role="מזכיר/ה מחוז תל אביב",
                     is_validated=True)
        user7 = User(username="TestSecretarBeerSheva",
                     email="TestSecretaryB@justice.com",
                     password=bcrypt.generate_password_hash("TestSecretary123!@#").decode('utf-8'),
                     role="מזכיר/ה מחוז באר שבע",
                     is_validated=True)

        users = [user1, user2, user3, user4, user5, user6, user7]
        for user in users:
            db.session.add(user)
        db.session.commit()

        vacation1 = Vacation(judge_id=1,
                                start_date=datetime.datetime.strptime('2022-05-28', '%Y-%m-%d'),
                                end_date=datetime.datetime.strptime('2022-05-30', '%Y-%m-%d'),
                                is_verified=True,
                                type='Short')
        vacation2 = Vacation(judge_id=1,
                                start_date=datetime.datetime.strptime('2022-06-08', '%Y-%m-%d'),
                                end_date=datetime.datetime.strptime('2022-06-18', '%Y-%m-%d'),
                                is_verified=False,
                                type='Long')
        vacation3 = Vacation(judge_id=1,
                                start_date=datetime.datetime.strptime('2022-05-02', '%Y-%m-%d'),
                                end_date=datetime.datetime.strptime('2022-05-04', '%Y-%m-%d'),
                                is_verified=True,
                                type='Short')
        vacation5 = Vacation(judge_id=4,
                                start_date=datetime.datetime.strptime('2022-05-22', '%Y-%m-%d'),
                                end_date=datetime.datetime.strptime('2022-05-25', '%Y-%m-%d'),
                                is_verified=True,
                                type='Short')
        vacation7 = Vacation(judge_id=3,
                                start_date=datetime.datetime.strptime('2022-05-22', '%Y-%m-%d'),
                                end_date=datetime.datetime.strptime('2022-05-25', '%Y-%m-%d'),
                                is_verified=True,
                                type='Short')

        vacations = [vacation1, vacation2, vacation3, vacation5, vacation7]
        for vacation in vacations:
            db.session.add(vacation)
        db.session.commit()
        return users, vacations

    @staticmethod
    def check_csv_imports(cases, judges, halls, rotation_dates):
        # Check if anything failed
        if not judges:
            print('Judges not imported correctly')
        if not halls:
            print('Halls not imported correctly')
        if not rotation_dates:
            print('Rotations not imported correctly')
        if not cases:
            print('Cases not imported correctly')

    @staticmethod
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
        c_weight = int.from_bytes(case_enrichment_df[pandas_query]['Weight'].values[0], 'little')

        return c_urg_level, c_duration, c_weight

    def add_cases_to_db(self):
        case_enrichment_df = pd.read_csv(self.case_enrichment_data_path).fillna('NO DATA')
        fake_cases_df = pd.read_csv(self.fake_cases_csv_path).fillna('NO DATA')
        for index, row in fake_cases_df.iterrows():
            main_type = row['Case_Main_Type']
            second_type = row['Secondary_Type']
            sub_type = row['Case_sub_type']
            location = row['Location']
            lawyer_1 = row['Lawyer_ID_1']
            lawyer_2 = row['Lawyer_ID_2']

            urg_level, duration, weight = self.get_case_db_data(case_enrichment_df, main_type,
                                                                                  second_type, sub_type)

            new_case = Case(first_type=main_type,
                            second_type=second_type,
                            third_type=sub_type,
                            urgency_level=urg_level,
                            duration=duration,
                            location=location,
                            weight=weight,
                            quarter_created=((datetime.datetime.now().month-1) // 3) + 1,
                            year_created=datetime.datetime.now().year,
                            lawyer_id_1=lawyer_1,
                            lawyer_id_2=lawyer_2)

            add_to_db(new_case)

        return True

    @staticmethod
    def create_user(email, role):
        default_password = 'Pass123987'
        hashed_password = bcrypt.generate_password_hash(default_password).decode('utf-8')
        username = email.split('@')[0]
        user = User(username=username, email=email, password=hashed_password, role=role, is_validated=True)
        add_to_db(user)
        return user

    def add_judges_to_db(self):
        judge_role = 'דיין/דיינת'
        judges_df = pd.read_csv(self.judge_data_csv_path)
        for index, row in judges_df.iterrows():
            judge_email = row['email']
            judge_user = User.query.filter_by(email=judge_email).first()
            if not judge_user:
                # create a user for Judge
                judge_user = self.create_user(judge_email, judge_role)
                judge = Judge(username=judge_user.username,
                              email=judge_email,
                              locations=row['Location'],
                              is_in_rotation=False,
                              total_weight='',
                              user_id=judge_user.id)
                add_to_db(judge)
            else:
                # judge already has user and user object in 'judge_user' just need to add location
                judge = Judge.query.filter_by(email=judge_email).first()
                judge.locations = judge.locations + ',' + row['Location']
                db.session.commit()

        return True

    def add_halls_to_db(self):
        halls_locations_df = pd.read_csv(self.halls_data_csv_path)
        for index, row in halls_locations_df.iterrows():
            hall = Hall(hall_number=row['Hall_id'],
                        location=row['Location'])
            add_to_db(hall)

        return True

    def add_lawyers_to_db(self):
        lawyers_df = pd.read_csv(self.lawyers_csv_path)
        for index, row in lawyers_df.iterrows():
            lawyer = Lawyer(name=row['Name'],
                            last_name=row['Last_name'],
                            lawyer_id=row['ID'],
                            mail=row['Mail'],
                            phone_number=row['Phone_number'])
            add_to_db(lawyer)

        return True

    def add_rotation_dates_to_db(self):
        rotation_df = pd.read_csv(self.rotation_data_csv_path)
        for index, row in rotation_df.iterrows():
            rotation = Rotation(judge_id=row['Judge_ID'],
                                start_date=datetime.datetime.strptime(row['Start_Date'], '%Y-%m-%d'),
                                end_date=datetime.datetime.strptime(row['End_Date'], '%Y-%m-%d'))
            add_to_db(rotation)

        return True
