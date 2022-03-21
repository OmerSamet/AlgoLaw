import datetime
from tabulate import tabulate
import pandas as pd

class Judge:
    def __init__(self, id):
        self.id = id
        self.casesSummons = []

    def add_summons(self, day, hall):
        self.casesSummons.append({day: hall})

# datetime(year, month, day, hour, minute, second)
startTime = datetime.datetime(2022, 3, 7, 9, 0, 0)
endTime = datetime.datetime(2022, 3, 7, 15, 00, 0)
  
# returns a timedelta object
totalTimeDay = endTime-startTime
print('Difference in hours: ', totalTimeDay)

# returns the difference of the time of the day
minutes = totalTimeDay.seconds / 60
print('Difference in minutes: ', minutes)

courtDuration = 35 # minutes
breakDuration = 10

numOfCasesDailyOneHall = minutes / (courtDuration + breakDuration)
print('Num of cases in one hall a day: ', numOfCasesDailyOneHall)

judges = [1,2,3,4,5,6,7,8,9,10]
halls = [1,2,3]
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']

TotalCasesWeekly = numOfCasesDailyOneHall * len(halls) * len(days)
TotalCasesWeeklyPerJudge = TotalCasesWeekly / len(judges)
print('TotalCasesWeeklyPerJudge: ', TotalCasesWeeklyPerJudge)

def schedule_judges(judges_ids):
    for day in days:
        for hall in halls:
            for judge in judges_ids:
                if(len(judge.casesScheduled) < numOfCasesDailyOneHall):
                    judge.add_summons(day,hall)


# 1 [(1, [1,1,1,1,1,1,1,1,1,1]), (2, [2,2,2,2,2,2,2,2,2,2,2]), (3, [3,3,3,3,3,3,3,3,3,3])]
# 2 [(1, [4,4,4,4,4,4,4,4,4,4]), (2, [5,5,5,5,5,5,5,5,5,5,5]), (3, [6,6,6,6,6,6,6,6,6,6])]
# 3 [(1, [7,7,7,7,7,7,7,7,7,7]), (2, [8,8,8,8,8,8,8,8,8,8,8]), (3, [9,9,9,9,9,9,9,9,9,9])]
# 4 [(1, [10,10,10,10,10,10,10,10,10,10]), (2, [1,1,1,1,1,2,2,2,2,2]), (3, [3,3,3,3,3,4,4,4,4,4])]
# 5 [(1, [5,5,5,5,5,6,6,6,6,6]), (2, [7,7,7,7,7,8,8,8,8,8,8]), (3, [9,9,9,9,9,10,10,10,10,10])]
