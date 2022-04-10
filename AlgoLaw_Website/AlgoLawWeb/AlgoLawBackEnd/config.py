# FILE NAMES #
import os
from AlgoLawWeb import app

JudgeDataDir = os.path.join(app.root_path, 'DB_DATA', 'Judge_Data.csv')
CaseDataDir = os.path.join(app.root_path, 'DB_DATA', 'Fake_case_data.csv')
CaseDBDataDir = os.path.join(app.root_path, 'DB_DATA', 'Case_Data.csv')
#
# if platform.system() == 'Windows':
#     JudgeDataDir = r'C:\Users\Chen\Desktop\AlgoLaw\DB_DATA\Judge_Data.csv'
#     CaseDataDir = r'C:\Users\Chen\Desktop\AlgoLaw\DB_DATA\Fake_case_data.csv'
#     CaseDBDataDir = r'C:\Users\Chen\Desktop\AlgoLaw\DB_DATA\Case_Data.csv'
# else:
#     JudgeDataDir = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/DB_DATA/Judge_Data.csv'
#     CaseDataDir = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/DB_DATA/Fake_case_data.csv'
#     CaseDBDataDir = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/DB_DATA/Ca' \
#                 r'se_Data.csv'
