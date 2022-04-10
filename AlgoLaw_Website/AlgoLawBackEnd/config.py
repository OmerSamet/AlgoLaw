# FILE NAMES #
import platform

if platform.system() == 'Windows':
    JudgeDataDir = r'C:\Users\Chen\Desktop\AlgoLaw\DB_DATA\Judge_Data.csv'
    CaseDataDir = r'C:\Users\Chen\Desktop\AlgoLaw\DB_DATA\Fake_case_data.csv'
    CaseDBDataDir = r'C:\Users\Chen\Desktop\AlgoLaw\DB_DATA\Case_Data.csv'
else:
    JudgeDataDir = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/DB_DATA/Judge_Data.csv'
    CaseDataDir = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/DB_DATA/Fake_case_data.csv'
    CaseDBDataDir = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/DB_DATA/Ca' \
                r'se_Data.csv'
