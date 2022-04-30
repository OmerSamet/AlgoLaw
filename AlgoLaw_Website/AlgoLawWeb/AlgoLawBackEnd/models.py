import time

import pandas as pd
from collections import defaultdict
from datetime import datetime
from AlgoLaw_Website.AlgoLawWeb import app
from AlgoLaw_Website.AlgoLawWeb.AlgoLawBackEnd.config import JudgeDataDir, CaseDataDir, CaseDBDataDir
from AlgoLaw_Website.AlgoLawWeb.models import Judge, Case, MeetingSchedule
import os


class DivJudge:
    def __init__(self, id, name, locations, is_in_rotation):
        self.id = id
        self.name = name
        self.locations = locations
        self.is_in_rotation = is_in_rotation
        self.weight_dict = defaultdict(int)  # dict -> location: weight
        self.cases = []

    def add_case(self, case):
        self.cases.append(case)
        self.weight_dict[case.location] += case.weight
        if case.location not in self.locations:
            self.locations.append(case.location)

    def get_weight(self):
        total_weight = 0
        for location in self.weight_dict.keys():
            total_weight += self.weight_dict[location]
        return total_weight

    def add_location(self, location):
        self.locations.append(location)


class DBReader:
    def __init__(self):
        self.judges = self.get_judges()
        self.cases = self.get_cases()

    def get_judges(self):
        judges = Judge.query.all()
        judges = self.create_judges(judges)
        return judges

    @staticmethod
    def create_judges(db_judges):
        judges = []
        for judge in db_judges:
            j_name = judge.username
            j_id = judge.id
            j_location = judge.locations
            j_location = j_location.split(',')
            divjudge = DivJudge(j_id, j_name, j_location, False)
            judges.append(divjudge)
        return judges

    @staticmethod
    def get_cases():
        cases_data = Case.query.all()
        meetings = MeetingSchedule.query.all()
        case_ids_with_meetings = [meeting.case_id for meeting in meetings]
        cases_without_meetings = [case for case in cases_data if case.id not in case_ids_with_meetings]
        return cases_without_meetings


class Divider:
    def __init__(self, judges, cases):
        self.judges = judges
        self.cases = cases

    def handle_cases(self):
        for case in self.cases:
            judge = self.send_case(case)
        self.write_csv()

    def send_case(self, case):
        relevant_judges = [judge for judge in self.judges if self.is_valid_judge(judge, case)]
        if not relevant_judges:
            return None

        sort_judges_by_weight = sorted(relevant_judges, key=lambda x: x.get_weight())
        sort_judges_by_weight[0].add_case(case)
        return sort_judges_by_weight[0]

    def calc_locations(self):
        locations_map = {'Haifa': 0,
                         'Tel Aviv': 0,
                         'Jerusalem': 0,
                         'Beer Sheva': 0}
        for judge_id in self.judges:
            judge_location_data = judge_id.weight_dict
            for location, amount in judge_location_data.items():
                locations_map[location] += amount
        return locations_map

    def is_valid_judge(self, judge, case):
        return self.valid_location(judge, case)

    @staticmethod
    def valid_location(judge, case):
        if case.location in judge.locations:
            return True
        return False

    def write_csv(self):
        output_path = os.path.join(app.config["OUTPUT_DIR"], 'output.csv')
        while os.path.exists(output_path):
            os.remove(output_path)
            time.sleep(1)
        with open(output_path, 'w', encoding='UTF8', newline='') as f:
            f.write('ID Case,ID judge,Location\n')
            for judge in self.judges:
                for case in judge.cases:
                    line = str(case.id) + ',' + str(judge.id) + ',' + case.location + '\n'
                    f.write(line)