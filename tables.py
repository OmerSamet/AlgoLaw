import os
import time
import csv
import pathlib


class Judge:
    def __init__(self, id, name, locations, is_in_rotation, total_weight, cases):
        self.id = id
        self.name = name
        self.locations = locations
        self.is_in_rotation = is_in_rotation
        self.total_weight = 0
        self.cases = []


    def add_case(self, Case):
        self.cases.append(Case)
        self.total_weight += Case.weight



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
                     'Jerusalem':0,
                     'Beer Sheva':0}
    for judge_id in judges_ids:
        judge_location_data = judge_id.get_locations
        for location, amount in judge_location_data.items():
            locations_map[location] += amount


def handle_cases(judges_ids, cases_ids):
    for case_id in cases_ids:
        send_case(judges_ids, case_id)


def compare_judges_weight(j1, j2):
    if j1.get_weigth() < j2.get_weigth():
        return -1
    elif j1.get_weigth() > j2.get_weigth():
        return 1
    else:
        return 0


def send_case(judges_ids, case_id):
    sort_judges_by_weight = judges_ids.sort(key=compare_judges_weight)
    for judge_id in sort_judges_by_weight:
        if is_valid_judge(judge_id, case_id):
            judge_id.add_case()
            return judge_id
    return None


def is_valid_judge(judge_id, case_id):
    return valid_location(judge_id, case_id)


def valid_location(judge_id, case_id):
    for case_location in case_id.get_locations():
        if case_location in judge_id.get_locations():
            return True
    return False


def write_csv(data):
    header = ['ID Case', 'ID judge', 'Location', 'Hall', 'Date', 'Time']
    with open('output.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)


def get_data(directory):
    file_list = []
    for i in os.listdir(directory):
        a = os.stat(os.path.join(directory, i))
        file_list.append([pathlib.Path(i).parent.resolve(), i, time.ctime(a.st_ctime),
                          time.ctime(a.st_mtime), time.ctime(a.st_atime)])
    return file_list


if __name__ == '__main__':
    judges_ids = get_data('judges.csv')
    cases_ids = get_data('cases.csv')

    result =
    write_csv(result)
