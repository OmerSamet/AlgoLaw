from collections import defaultdict

from AlgoLaw_Website.AlgoLawWeb.AlgoLawBackEnd.models import DBReader, Divider
from AlgoLaw_Website.AlgoLawWeb import db, app
from AlgoLaw_Website.AlgoLawWeb.models import Hall, Case, CaseJudgeLocation, MeetingSchedule, Meeting, Vacation, Rotation, SickDay
import datetime
import calendar
import enum
from AlgoLaw_Website.AlgoLawWeb.utilities import add_to_db, insert_output_to_db, DayToHallToJudgeJerusalem
import os
from flask import flash


class JerusalemTimeSlots(enum.Enum):
    nine_to_nine_thirty_five = '09:00-09:35'
    nine_forty_five_to_ten_twenty = '09:45-10:20'
    ten_thirty_to_eleven_o_five = '10:30-11:05'
    eleven_fifteen_to_eleven_fifty = '11:15-11:50'
    twelve_to_twelve_thirty_five = '12:00-12:35'
    twelve_forty_five_to_one_twenty = '12:45-13:20'
    one_thirty_to_two_o_five = '13:30-14:05'
    two_fifteen_to_two_fifty = '14:15-14:50'


class JerusalemDay:
    def __init__(self, date):
        self.date = date
        self.day_of_the_week = date.isoweekday()
        self.schedule = self.create_day_schedule()

    @staticmethod
    def timeslot_in_first_half_of_day(time_slot):
        slots = list(JerusalemTimeSlots)
        slot_index = slots.index(time_slot)
        if slot_index < len(slots) / 2:
            return True
        else:
            return False

    def create_day_schedule(self):
        schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        for hall, judges in DayToHallToJudgeJerusalem[self.day_of_the_week].items():
            for time_slot in JerusalemTimeSlots:
                if self.timeslot_in_first_half_of_day(time_slot):
                    schedule[hall][time_slot.value][judges[0]] = ''
                else:
                    schedule[hall][time_slot.value][judges[1]] = ''

        return schedule


class LocationScheduler:
    def __init__(self, cases, location):
        self.cases = cases
        self.halls = self.get_halls(location)

    @staticmethod
    def get_halls(location):
        return Hall.query.filter_by(location=location).all()

    @staticmethod
    def get_workdays(num_days, year, month):
        work_days = []
        for day in range(1, num_days + 1):
            day_date = datetime.date(year, month, day)
            if day_date.isoweekday() in DayToHallToJudgeJerusalem.keys() and day_date >= datetime.datetime.now().date():
                work_days.append(day_date)
        return work_days

    def get_next_90_dates(self):
        year = datetime.datetime.now().year
        quarterly_dates = []
        for i in range(0, 4):
            month = datetime.datetime.now().month + i
            num_days = calendar.monthrange(year, month)[1]
            work_days = self.get_workdays(num_days, year, month)
            quarterly_dates.extend(work_days)
            if len(quarterly_dates) >= 90:
                break

        return quarterly_dates

    def init_schedule(self, halls):
        '''
        :input: halls -> list of hall objects
        :description: Function returns dict of dates of quarter to empty lists,
                      we will use this function for each hall so every hall will have a dict of dates
                      and every date will have a list of HallSchedule

                      empty_schedule is a dict that is built like this:
                      {date: {time_slot: {hall_id: case_id,
                                            hall_id: case_id
                                            hall_id: case_id
                                            ...},
                                {time_slot: {hall_id: case_id,
                                            hall_id: case_id
                                            hall_id: case_id
                                            ...},
                                ...
                                },
                        date2: {time_slot: {hall_id: case_id,
                                            hall_id: case_id
                                            hall_id: case_id
                                            ...},
                                {time_slot: {hall_id: case_id,
                                            hall_id: case_id
                                            hall_id: case_id
                                            ...},
                                ...
                                },
                                ...

        :return: empty_schedule
        '''
        quarterly_dates = self.get_next_90_dates()
        empty_schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(Case)))
        empty_case = Case()
        for date in quarterly_dates:
            for time_slot in JerusalemTimeSlots:
                for day_num, hall_dict in DayToHallToJudgeJerusalem.items():
                    for hall_num, judges in hall_dict.items():
                        empty_schedule[str(date)][time_slot.value][hall_num] = empty_case

        return empty_schedule

    def lawyer_is_not_in_different_city(self, date, lawyer_id_1, lawyer_id_2, location):
        if lawyer_id_1 != '' and lawyer_id_2 != '':
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_1 == lawyer_id_1,
                                                                              MeetingSchedule.date == date,
                                                                              MeetingSchedule.location != location).all()
            lawyers_2_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_2 == lawyer_id_2,
                                                                              MeetingSchedule.date == date,
                                                                              MeetingSchedule.location != location).all()
            return len(lawyers_1_cases_that_day) == 0 and len(lawyers_2_cases_that_day) == 0
        if lawyer_id_1 != '' and lawyer_id_2 == '':
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_1 == lawyer_id_1,
                                                                              MeetingSchedule.date == date,
                                                                              MeetingSchedule.location != location).all()
            return len(lawyers_1_cases_that_day) == 0
        if lawyer_id_1 == '' and lawyer_id_2 != '':
            lawyers_2_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_2 == lawyer_id_2,
                                                                              MeetingSchedule.date == date,
                                                                              MeetingSchedule.location != location).all()
            return len(lawyers_2_cases_that_day) == 0
        return True


    def lawyer_is_not_booked(self, time_slot , lawyer_id_1 , lawyer_id_2 , location):
        if (lawyer_id_1 != '') and (lawyer_id_2 != ''):
            start_time, end_time = time_slot.split('-')
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_1 == lawyer_id_1,
                                                                              MeetingSchedule.start_time == start_time ,
                                                                              MeetingSchedule.location == location).all()
            lawyers_2_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_2 == lawyer_id_2,
                                                                MeetingSchedule.start_time == start_time,
                                                                MeetingSchedule.location == location).all()
            return (len(lawyers_1_cases_that_day) == 0) and (len(lawyers_2_cases_that_day) == 0)
        if (lawyer_id_1 != '') and (lawyer_id_2 == ''):
            start_time, end_time = time_slot.split('-')
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_1 == lawyer_id_1,
                                                                              MeetingSchedule.start_time == start_time ,
                                                                              MeetingSchedule.location == location).all()
            return (len(lawyers_1_cases_that_day) == 0)
        if  (lawyer_id_2 != '') and (lawyer_id_1 == '') :
            start_time, end_time = time_slot.split('-')
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_2 == lawyer_id_2,
                                                                              MeetingSchedule.start_time == start_time ,
                                                                              MeetingSchedule.location == location).all()
            return (len(lawyers_1_cases_that_day) == 0)
        return True


class JerusalemScheduler(LocationScheduler):
    def __init__(self, cases):
        self.location = 'Jerusalem'
        LocationScheduler.__init__(self, cases, self.location)
        self.halls = self.get_halls(self.location)
        self.hall_schedules = self.init_schedule(self.halls)

    def order_cases(self):
        return sorted(self.cases, key=lambda x: x.urgency_level, reverse=True)

    @staticmethod
    def timeslot_in_first_half_of_day(time_slot):
        slots = list(JerusalemTimeSlots)
        slot_index = slots.index(time_slot)
        if slot_index < len(slots) / 2:
            return True
        else:
            return False

    def relevant_judge(self, judge_id, date, hall_number, time_slot):
        day_of_week = date.isoweekday()
        if self.timeslot_in_first_half_of_day(time_slot):
            return judge_id == DayToHallToJudgeJerusalem[day_of_week][hall_number][0]
        else:
            return judge_id == DayToHallToJudgeJerusalem[day_of_week][hall_number][1]

    def isDateBetweenDates(self, date, startDate, endDate):
        datetime_date = datetime.datetime(date.year , date.month , date.day)
        return (datetime_date > startDate) and ( datetime_date < endDate)

    def judgeIsAvailable(self, judge_id, date):
        vacations = db.session.query(Vacation).filter(Vacation.is_verified).all()
        for vac in vacations:
            if vac.judge_id == judge_id and self.isDateBetweenDates(date , vac.start_date , vac.end_date):
                return False

        sick_days = db.session.query(SickDay).filter(SickDay.is_verified).all()
        for sick_day in sick_days:
            if sick_day.judge_id == judge_id and self.isDateBetweenDates(date, sick_day.start_date, sick_day.end_date):
                return False

        rotations = db.session.query(Rotation).all()
        for rot in rotations:
            if rot.judge_id == judge_id and self.isDateBetweenDates(date, rot.start_date, rot.end_date):
                return False

        return True

    def add_meeting_to_schedule(self, case, date, time_slot, hall_number, judge_id, lawyer_id_1, lawyer_id_2):
        date_obj = date
        start_time, end_time = time_slot.split('-')
        # add meeting to DB
        quarter = ((date_obj.month - 1) // 3) + 1
        meeting = Meeting(case_id=case.id,
                          quarter=quarter,
                          year=date_obj.year)
        add_to_db(meeting)
        meeting_id = Meeting.query.filter(Meeting.case_id == case.id,
                                          Meeting.quarter == quarter,
                                          Meeting.year == date_obj.year).first().id
        # get hall id from hall number
        hall = Hall.query.filter(Hall.location == case.location,
                                 Hall.hall_number == hall_number).first()

        # add meeting scheduling
        meeting_schedule = MeetingSchedule(case_id=case.id,
                                     hall_id=hall.id,
                                     date=date_obj,
                                     judge_id=judge_id,
                                     start_time=start_time,
                                     end_time=end_time,
                                     meeting_id=meeting_id,
                                     lawyer_id_1=lawyer_id_1,
                                     lawyer_id_2 = lawyer_id_2,
                                     location='Jerusalem')
        add_to_db(meeting_schedule)

    def get_case_id_to_judge_id(self):
        case_judge_locations = db.session.query(CaseJudgeLocation).filter(
            CaseJudgeLocation.case_id.in_([case.id for case in self.cases])).all()
        case_id_to_judge_id = defaultdict(int)
        for case_judge_location in case_judge_locations:
            case_id_to_judge_id[case_judge_location.case_id] = case_judge_location.judge_id
        return case_id_to_judge_id

    def date_relevant_for_case(self, j_date, judge_id, case):
        '''
        input - date, judge_id

        checks if judge of case is working on this date and returns True if yes False if no
        '''
        for hall_number, time_slot_dict in j_date.schedule.items():
            for time_slot, judge_dict in time_slot_dict.items():
                lawyers_available = (self.lawyer_is_not_booked(time_slot,case.lawyer_id_1, case.lawyer_id_2, 'Jerusalem'))
                if lawyers_available:
                    for judge, case_id in judge_dict.items():
                        if judge_id == judge and self.judgeIsAvailable(judge_id, j_date.date):
                            if case_id == '':
                                return True, hall_number, time_slot
        return False, False, False

    def schedule_cases(self):
        '''
        MAIN FUNCTION
        :return:
        '''
        ordered_cases = self.order_cases()
        case_id_to_judge_id = self.get_case_id_to_judge_id()
        quarterly_dates = self.get_next_90_dates()
        quarterly_J_days = [JerusalemDay(date) for date in quarterly_dates]
        # case object
        i = 1
        for case in ordered_cases:
            print('Starting Jerusalem case {} / {} scheduling'.format(i, len(ordered_cases)))

            judge_id = case_id_to_judge_id[case.id]
            been_placed_in_calendar = False
            for J_date in quarterly_J_days:
                if been_placed_in_calendar:
                    break
                lawyers_available = self.lawyer_is_not_in_different_city(J_date.date, case.lawyer_id_1, case.lawyer_id_2, 'Jerusalem')
                if lawyers_available:
                    relevant, hall_number, time_slot = self.date_relevant_for_case(J_date, judge_id ,case)
                    if relevant:
                        print('Done - Found! Jerusalem case relevancy {} / {}'.format(i, len(ordered_cases)))
                        been_placed_in_calendar = True
                        J_date.schedule[hall_number][time_slot][judge_id] = case.id
                        print('Adding Jerusalem case  {} / {} to DB'.format(i, len(ordered_cases)))
                        self.add_meeting_to_schedule(case, J_date.date, time_slot, hall_number,
                                                     case_id_to_judge_id[case.id],case.lawyer_id_1 , case.lawyer_id_2)
                        print('Done - Adding Jerusalem case  {} / {} to DB'.format(i, len(ordered_cases)))

            if not been_placed_in_calendar:
                print('Case {} has not been placed in calendar!'.format(case.id))
            print('Done - Jerusalem case {} / {} scheduling'.format(i, len(ordered_cases)))
            i += 1

class MeetingScheduler:
    def __init__(self, start_date):
        self.start_date = start_date  # start of quarter
        self.quarter = ((start_date.month - 1) // 3) + 1
        self.output_path = os.path.join(app.config["OUTPUT_DIR"], 'output.csv')
        self.year = start_date.year
        self.location_to_cases = self.divide_cases_to_location()  # dict { 'location': [cases] ...

    def get_uploaded_cases(self):
        '''
        using self.quarter loads relevant cases
        :return: cases -> list of Case objects (AlgoLawWeb.models.Case)
        '''

        cases = db.session.query(Case).filter(
            Case.quarter_created == self.quarter,
            Case.year_created == self.year).all()

        case_ids = [case.id for case in cases]

        cases_with_meetings = MeetingSchedule.query.filter(MeetingSchedule.case_id.in_(case_ids)).all()
        case_ids_with_meetings = [meeting.case_id for meeting in cases_with_meetings]
        case_ids_without_meetings = [case_id for case_id in case_ids if case_id not in case_ids_with_meetings]

        cases = db.session.query(Case).filter(Case.id.in_(case_ids_without_meetings)).all()

        return cases

    def divide_cases_to_location(self):
        cases = self.get_uploaded_cases()
        print('Amount of Cases got: {}'.format(len(cases)))
        location_to_cases = defaultdict(list)  # dict of location to case list -> {location_name_str: [Case], ...
        for case in cases:
            location_to_cases[case.location].append(case)

        return location_to_cases

    def schedule_jerusalem_cases(self):
        print('Starting Jerusalem scheduling')
        print('Getting Jerusalem cases')
        j_scheduler = JerusalemScheduler(self.location_to_cases['ירושלים'])
        print('Done - Getting Jerusalem cases')
        j_scheduler.schedule_cases()
        print('Done - Jerusalem scheduling')

