import pandas as pd
from collections import defaultdict
from datetime import datetime
from AlgoLawWeb import app
from AlgoLawWeb.AlgoLawBackEnd.config import JudgeDataDir, CaseDataDir, CaseDBDataDir
import os

class Judge:
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


class Case:
    def __init__(self, id, first_type, second_type, third_type, urgency_level, duration, location, weight):
        self.id = id
        self.first_type = first_type
        self.second_type = second_type
        self.third_type = third_type
        self.urgency_level = urgency_level
        self.duration = duration
        self.location = location
        self.weight = weight
        self.quarter = ((datetime.now().month-1) // 3) + 1
        self.status = True  # True = is open, False = Done


class DBReader:
    def __init__(self):
        self.judges = self.get_judges()
        self.cases = self.get_cases()

    def get_judges(self):
        judges_data = pd.read_csv(JudgeDataDir)
        judges = self.create_judges(judges_data)
        return judges

    def create_judges(self, judges_data):
        judges = []
        for index, row in judges_data.iterrows():
            j_name = row['Judge_name']
            j_id = row['Judge_ID']
            j_location = row['Location']
            judge_exists = self.check_if_judge_exists_already(j_id, judges)
            if judge_exists:
                judge_exists.add_location(j_location)
            else:
                judge = Judge(j_id, j_name, [j_location], False)
                judges.append(judge)
        return judges

    @staticmethod
    def check_if_judge_exists_already(j_id, judges):
        for judge in judges:
            if judge.id == j_id:
                return judge
        return False

    def get_cases(self):
        cases_data = pd.read_csv(CaseDataDir)
        cases_ids = self.create_cases(cases_data)
        return cases_ids

    def create_cases(self, cases_data):
        cases = []
        # Read DB Data to get values
        case_db_data = pd.read_csv(CaseDBDataDir)

        for index, row in cases_data.iterrows():
            c_id = index + 1
            c_main_type = row['Case_Main_Type']
            c_secondary_type = row['Secondary_Type']
            c_sub_type = row['Case_sub_type']

            c_urg_level, c_duration, c_location, c_weight = self.get_case_db_data(case_db_data, c_main_type,
                                                                             c_secondary_type, c_sub_type)

            case = Case(c_id, c_main_type, c_secondary_type, c_sub_type, c_urg_level, c_duration, c_location, c_weight)
            cases.append(case)
        return cases

    @staticmethod
    def get_case_db_data(case_db_data, c_main_type, c_secondary_type, c_sub_type):
        if type(c_sub_type) == str:
            pandas_query = (case_db_data['Main_Type'] == c_main_type) & (
                        case_db_data['Secondary_Type'] == c_secondary_type) & (
                                   case_db_data['Sub_Type'] == c_sub_type)
        else:
            pandas_query = (case_db_data['Main_Type'] == c_main_type) & (
                    case_db_data['Secondary_Type'] == c_secondary_type)

        c_urg_level = case_db_data[pandas_query]['Urgency_Level'].values[0]
        c_duration = case_db_data[pandas_query]['Duration'].values[0]
        c_location = case_db_data[pandas_query]['Location'].values[0]
        c_weight = case_db_data[pandas_query]['Weight'].values[0]

        return c_urg_level, c_duration, c_location, c_weight


class Divider:
    def __init__(self, judges, cases):
        self.judges = judges
        self.cases = cases

    def handle_cases(self):
        for case in self.cases:
            judge = self.send_case(case)
        self.write_csv()

    def send_case(self, case):
        case.location = self.get_case_location(case)
        relevant_judges = [judge for judge in self.judges if self.is_valid_judge(judge, case)]
        if not relevant_judges:
            return None

        sort_judges_by_weight = sorted(relevant_judges, key=lambda x: x.get_weight())
        sort_judges_by_weight[0].add_case(case)
        return sort_judges_by_weight[0]

    def get_case_location(self, case):
        locations_map = self.calc_locations()
        if case.location in locations_map.keys():
            return case.location
        elif case.location == '/ Not jerusalem':
            del (locations_map['Jerusalem'])
        elif case.location == 'Tel Aviv / Jerusalem':
            del (locations_map['Beer Sheva'])
            del (locations_map['Haifa'])
        min_location = min(locations_map, key=locations_map.get)
        return min_location

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
        with open(output_path, 'w', encoding='UTF8', newline='') as f:
            f.write('ID Case,ID judge,Location\n')
            for judge in self.judges:
                for case in judge.cases:
                    line = str(case.id) + ',' + str(judge.id) + ',' + case.location + '\n'
                    f.write(line)