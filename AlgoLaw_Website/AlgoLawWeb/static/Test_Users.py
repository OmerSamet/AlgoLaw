'''
Users for test of roles

Username: TestJudge
email: TestJudge@justice.com
password: TestJudge123!@#
Role: Judge


Username: TestSecretary
email: TestSecretary@justice.com
password: TestSecretary123!@#
Role: Secretary



Username: TestMaster
email: TestMaster@justice.com
password: TestMaster123!@#
Role: Master

'''


'''
FAKE CASES

CASE 1


'''
from AlgoLawWeb.models import User, Post, ROLES, JudgeToVaca
from AlgoLawWeb import db, bcrypt
import datetime
db.drop_all()
db.create_all()

user1 = User(username="TestJudge",
             email="TestJudge@justice.com",
             password=bcrypt.generate_password_hash("TestJudge123!@#").decode('utf-8'),
             role="דיין/דיינת")
user2 = User(username="TestSecretary",
             email="TestSecretary@justice.com",
             password=bcrypt.generate_password_hash("TestSecretary123!@#").decode('utf-8'),
             role="מזכיר/מזכירה")
user3 = User(username="TestMaster",
             email="TestMaster@justice.com",
             password=bcrypt.generate_password_hash("TestMaster123!@#").decode('utf-8'),
             role="הנהלה")
user4 = User(username="TestJudge2",
             email="TestJudge2@justice.com",
             password=bcrypt.generate_password_hash("TestJudge123!@#").decode('utf-8'),
             role="דיין/דיינת")
users = [user1, user2, user3, user4]
for user in users:
    db.session.add(user)
db.session.commit()

vacation1 = JudgeToVaca(judge_id=1,
                        start_date=datetime.datetime.strptime('2022-03-28','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-03-30','%Y-%m-%d'),
                        is_verified=True,
                        type='Short')
vacation2 = JudgeToVaca(judge_id=1,
                        start_date=datetime.datetime.strptime('2022-04-08','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-04-18','%Y-%m-%d'),
                        is_verified=False,
                        type='Long')
vacation3 = JudgeToVaca(judge_id=1,
                        start_date=datetime.datetime.strptime('2022-04-02','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-04-04','%Y-%m-%d'),
                        is_verified=True,
                        type='Short')
vacation4 = JudgeToVaca(judge_id=1,
                        start_date=datetime.datetime.strptime('2022-03-02','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-03-20','%Y-%m-%d'),
                        is_verified=True,
                        type='Long')
vacation5 = JudgeToVaca(judge_id=1,
                        start_date=datetime.datetime.strptime('2022-04-22','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-04-25','%Y-%m-%d'),
                        is_verified=True,
                        type='Short')
vacation6 = JudgeToVaca(judge_id=4,
                        start_date=datetime.datetime.strptime('2022-03-02','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-03-20','%Y-%m-%d'),
                        is_verified=True,
                        type='Long')
vacation7 = JudgeToVaca(judge_id=4,
                        start_date=datetime.datetime.strptime('2022-04-22','%Y-%m-%d'),
                        end_date=datetime.datetime.strptime('2022-04-25','%Y-%m-%d'),
                        is_verified=True,
                        type='Short')

vacations = [vacation1,vacation2,vacation3,vacation4,vacation5]
for vacation in vacations:
    db.session.add(vacation)
db.session.commit()

