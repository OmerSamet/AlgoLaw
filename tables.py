import csv
import pandas as pd


class Judge:
    def __init__(self, id, name, locations, is_in_rotation):
        self.id = id
        self.name = name
        self.locations = locations
        self.is_in_rotation = is_in_rotation
        self.total_weight = self.create_weight_dict()
        self.cases = []

    def create_weight_dict(self):
        location_weight_dict = dict()
        for location in self.locations:
            location_weight_dict[location] = 0

        return location_weight_dict

    def add_case(self, Case):
        self.cases.append(Case)
        self.total_weight[Case.location] += Case.weight

    def get_weight(self, location):
        return self.total_weight[location]

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
        judge_location_data = judge_id.get_locations
        for location, amount in judge_location_data.items():
            locations_map[location] += amount


def handle_cases(judges_ids, cases_ids):
    for case_id in cases_ids:
        judge_id = send_case(judges_ids, case_id)


# def compare_judges_weight(j1, j2, location=location):
#     if j1.get_weight() < j2.get_weight():
#         return -1
#     elif j1.get_weight() > j2.get_weight():
#         return 1
#     else:
#         return 0

def send_case(judges_ids, case_id):
    relevant_judges = [judge_id for judge_id in judges_ids if is_valid_judge(judge_id, case_id)]
    if not relevant_judges:
        return None
    sort_judges_by_weight = sorted(relevant_judges, key=lambda x: x.get_weight(case_id.location))
    sort_judges_by_weight[0].add_case(case_id)
    return sort_judges_by_weight[0]


def is_valid_judge(judge_id, case_id):
    return valid_location(judge_id, case_id)


def valid_location(judge_id, case_id):
    for case_location in case_id.get_locations():
        if case_location in judge_id.get_locations():
            return True
    return False


def write_csv(judges_ids):
    # Write Judges and cases division
    header = ['ID Case', 'ID judge', 'Location']
    with open('output.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for judge in judges_ids:
            for case in judge.cases:
                line = str(case.id) + ',' + str(judge.id) + ',' + case.location + '\n'
                writer.writerow(line)

    # Write Judges and weight division
    header = ['ID judge', 'location', 'weight']
    with open('judge_output.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for judge in judges_ids:
            judge_weight_dict = judge.total_weight
            for location, weight in judge.total_weight.items():
                line = str(judge.id) + ',' + location + ',' + str(weight)
                writer.writerow(line)


def check_if_judge_exists_already(j_id, judges):
    for judge in judges:
        if judge.id == j_id:
            return judge

    return False


def create_judges(judges_data):
    judges = []
    for index, row in judges_data.iterrows():
        if index > 0:
            j_name = row['Judge_name']
            j_id = row['Judge_ID']
            j_location = row['location']
            judge_exists = check_if_judge_exists_already(j_id, judges)
            if judge_exists:
                judge_exists.add_location(j_location)
            else:
                judge = Judge(j_id, j_name, j_location, [], False)
                judges.append(judge)
    print(judges)
    return judges


def create_cases(cases_data):
    cases = []
    for index, row in cases_data.iterrows():
        c_id = row['ID']
        c_main_type = row['Main_Type']
        c_secondary_type = row['Secondary_Type']
        c_sub_type = row['Sub_Type']
        c_urg_level = row['Urgency_Level']
        c_duration = row['Duration']
        c_location = row['Location']
        c_weight = row['Weight']
        case = Case(c_id, c_main_type, c_secondary_type, c_sub_type, c_urg_level, c_duration, c_location, c_weight)
        cases.append(case)
    print(cases)
    return cases


if __name__ == '__main__':
    judges_data = pd.read_csv('DB_DATA/Judge_Data.csv')
    print(judges_data)
    cases_data = pd.read_csv('DB_DATA/Case_Data.csv')
    print(cases_data)
    judges_ids = create_judges(judges_data)
    cases_ids = create_cases(cases_data)
    handle_cases(judges_ids, cases_ids)
    write_csv(judges_ids)
