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

from AlgoLawWeb import db
db.drop_all()
db.create_all()

from AlgoLawWeb.models import User, Post, ROLES, JudgeToVaca

user1=User(username="TestJudge",email="TestJudge@justice.com",password="TestJudge123!@#",role="דיין/דיינת")
user2=User(username="TestSecretary",email="TestSecretary@justice.com",password="TestSecretary123!@#",role="מזכיר/מזכירה")
user3=User(username="TestMaster",email="TestMaster@justice.com",password="TestMaster123!@#",role="הנהלה")
db.session.add(user1)
db.session.add(user2)
db.session.add(user3)
db.session.commit()

'''


'''
FAKE CASES

CASE 1


'''