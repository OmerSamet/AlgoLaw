import csv
import pandas as pd
from collections import defaultdict


class Judge:
    def __init__(self, id, name, locations, is_in_rotation):
        self.id = id
        self.name = name
        self.locations = locations
        self.is_in_rotation = is_in_rotation
        self.total_weight = defaultdict(int)
        self.cases = []

    def add_case(self, case):
        self.cases.append(case)
        self.total_weight[case.location] += case.weight
        if case.location not in self.locations:
            self.locations.append(case.location)

    def get_weight(self, location):
        if location in self.total_weight.keys():
            return self.total_weight[location]
        else:
            return 0

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


def calc_locations(judges_ids):
    locations_map = {'Haifa': 0,
                     'Tel Aviv': 0,
                     'Jerusalem': 0,
                     'Beer Sheva': 0}
    for judge_id in judges_ids:
        judge_location_data = judge_id.total_weight
        for location, amount in judge_location_data.items():
            locations_map[location] += amount
    return locations_map


def get_case_location(judges_ids, not_jerusalem=False, j_or_t=False):
    '''
    :param judges_ids: list of Judge objects
    :param not_jerusalem: flag - if true then remove Jerusalem key from location dict so cannot return jerusalem location
    :param j_or_t: flag - if true then remove haifa and beer sheva from dict so return tel aviv or jerusalem
    :return: location with least weight
    '''
    locations_map = calc_locations(judges_ids)
    if not_jerusalem:
        del(locations_map['Jerusalem'])
    elif j_or_t:
        del (locations_map['Beer Sheva'])
        del (locations_map['Haifa'])
    min_location = min(locations_map, key=locations_map.get)
    return min_location


def handle_cases(judges_ids, cases_ids):
    for case_id in cases_ids:
        judge_id = send_case(judges_ids, case_id)
        if judge_id is None:
            print('got here')


# def compare_judges_weight(j1, j2, location=location):
#     if j1.get_weight() < j2.get_weight():
#         return -1
#     elif j1.get_weight() > j2.get_weight():
#         return 1
#     else:
#         return 0

def send_case(judges_ids, case_id):
    # Check if case has location already or not
    if pd.isna(case_id.location):
        case_id.location = get_case_location(judges_ids)
    elif case_id.location == '/ Not jerusalem':
        case_id.location = get_case_location(judges_ids, not_jerusalem=True)
    elif case_id.location == 'Tel Aviv / Jerusalem':
        case_id.location = get_case_location(judges_ids, j_or_t=True)

    relevant_judges = [judge_id for judge_id in judges_ids if is_valid_judge(judge_id, case_id)]
    if not relevant_judges:
        return None

    sort_judges_by_weight = sorted(relevant_judges, key=lambda x: x.get_weight(case_id.location))
    sort_judges_by_weight[0].add_case(case_id)
    return sort_judges_by_weight[0]


def is_valid_judge(judge_id, case_id):
    return valid_location(judge_id, case_id)


def valid_location(judge_id, case_id):
    if case_id.location in judge_id.locations:
        return True
    return False


def write_csv(judges_ids):
    # Write Judges and cases division
    header = []
    with open('output.csv', 'w', encoding='UTF8', newline='') as f:
        f.write('ID Case,ID judge,Location\n')
        for judge in judges_ids:
            for case in judge.cases:
                line = str(case.id) + ',' + str(judge.id) + ',' + case.location + '\n'
                f.write(line)

    # Write Judges and weight division
    with open('judge_output.csv', 'w', encoding='UTF8', newline='') as f:
        f.write('ID judge,location,weight\n')
        for judge in judges_ids:
            for location, weight in judge.total_weight.items():
                line = str(judge.id) + ',' + location + ',' + str(weight) + '\n'
                f.write(line)


def check_if_judge_exists_already(j_id, judges):
    for judge in judges:
        if judge.id == j_id:
            return judge

    return False


def create_judges(judges_data):
    judges = []
    for index, row in judges_data.iterrows():
        j_name = row['Judge_name']
        j_id = row['Judge_ID']
        j_location = row['Location']
        judge_exists = check_if_judge_exists_already(j_id, judges)
        if judge_exists:
            judge_exists.add_location(j_location)
        else:
            judge = Judge(j_id, j_name, [j_location], False)
            judges.append(judge)
    print(judges)
    return judges


def get_case_db_data(case_db_data, c_main_type, c_secondary_type, c_sub_type):
    if type(c_sub_type) == str:
        pandas_query = (case_db_data['Main_Type'] == c_main_type) & (case_db_data['Secondary_Type'] == c_secondary_type) & (
                    case_db_data['Sub_Type'] == c_sub_type)
    else:
        pandas_query = (case_db_data['Main_Type'] == c_main_type) & (
                    case_db_data['Secondary_Type'] == c_secondary_type)
    c_urg_level = case_db_data[pandas_query]['Urgency_Level'].values[0]
    c_duration = case_db_data[pandas_query]['Duration'].values[0]
    c_location = case_db_data[pandas_query]['Location'].values[0]
    c_weight = case_db_data[pandas_query]['Weight'].values[0]

    return c_urg_level, c_duration, c_location, c_weight


def create_cases(cases_data):
    cases = []
    # Read DB Data to get values
    case_db_data = pd.read_csv('DB_DATA/Case_Data.csv')
    for index, row in cases_data.iterrows():
        c_id = index + 1
        c_main_type = row['Case_Main_Type']
        c_secondary_type = row['Secondary_Type']
        c_sub_type = row['Case_sub_type']

        c_urg_level, c_duration, c_location, c_weight = get_case_db_data(case_db_data, c_main_type, c_secondary_type, c_sub_type)

        case = Case(c_id, c_main_type, c_secondary_type, c_sub_type, c_urg_level, c_duration, c_location, c_weight)
        cases.append(case)
    print(cases)
    return cases


if __name__ == '__main__':
    judges_data = pd.read_csv('DB_DATA/Judge_Data.csv')
    cases_data = pd.read_csv('DB_DATA/Fake_case_data.csv')
    judges_ids = create_judges(judges_data)
    cases_ids = create_cases(cases_data)
    handle_cases(judges_ids, cases_ids)
    write_csv(judges_ids)
