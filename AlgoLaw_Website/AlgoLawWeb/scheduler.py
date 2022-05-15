from collections import defaultdict

from AlgoLaw_Website.AlgoLawWeb.AlgoLawBackEnd.models import DBReader, Divider
from AlgoLaw_Website.AlgoLawWeb import db, app
from AlgoLaw_Website.AlgoLawWeb.models import Hall, Case, CaseJudgeLocation, MeetingSchedule, Meeting, Vacation\
    , Rotation, SickDay
import datetime
import calendar
import enum
from AlgoLaw_Website.AlgoLawWeb.utilities import add_to_db, DayToHallToJudgeJerusalem, DayToHallToJudgeTelAviv
import os
from flask import flash


class TimeSlot(enum.Enum):
    nine_to_nine_thirty_five = '09:00-09:35'
    nine_forty_five_to_ten_twenty = '09:45-10:20'
    ten_thirty_to_eleven_o_five = '10:30-11:05'
    eleven_fifteen_to_eleven_fifty = '11:15-11:50'
    twelve_to_twelve_thirty_five = '12:00-12:35'
    twelve_forty_five_to_one_twenty = '12:45-13:20'
    one_thirty_to_two_o_five = '13:30-14:05'
    two_fifteen_to_two_fifty = '14:15-14:50'


class Day:
    def __init__(self, date, day_to_hall_to_judge ):
        self.date = date
        self.day_of_the_week = date.isoweekday()
        self.schedule = self.create_day(day_to_hall_to_judge)

    @staticmethod
    def timeslot_in_first_half_of_day(time_slot):
        slots = list(TimeSlot)
        slot_index = slots.index(time_slot)
        if slot_index < len(slots) / 2:
            return True
        else:
            return False

    def create_day(self, day_to_hall_to_judge):
        schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        for hall, judges in day_to_hall_to_judge[self.day_of_the_week].items():
            for time_slot in TimeSlot:
                if self.timeslot_in_first_half_of_day(time_slot):
                    schedule[hall][time_slot.value][judges[0]] = ''
                else:
                    schedule[hall][time_slot.value][judges[1]] = ''

        return schedule

    def create_day_schedule(self):
        schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(str)))
        for hall, judges in DayToHallToJudgeJerusalem[self.day_of_the_week].items():
            for time_slot in TimeSlot:
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
    def get_workdays(num_days, year, month, day_to_hall_to_judge):
        work_days = []
        for day in range(1, num_days + 1):
            day_date = datetime.date(year, month, day)
            if day_date.isoweekday() in day_to_hall_to_judge.keys() and day_date >= datetime.datetime.now().date():
                work_days.append(day_date)
        return work_days

    def order_cases(self):
        return sorted(self.cases, key=lambda x: x.urgency_level, reverse=True)

    def get_next_90_dates(self, day_to_hall_to_judge):
        year = datetime.datetime.now().year
        quarterly_dates = []
        for i in range(0, 4):
            month = datetime.datetime.now().month + i
            num_days = calendar.monthrange(year, month)[1]
            work_days = self.get_workdays(num_days, year, month,day_to_hall_to_judge)
            quarterly_dates.extend(work_days)
            if len(quarterly_dates) >= 90:
                break

        return quarterly_dates
    '''
        def get_quarterly_dates(self, day_to_hall_to_judge):
        year = datetime.datetime.now().year
        quarterly_dates = []
        for i in range(0, 3):
            month = datetime.datetime.now().month + i
            num_days = calendar.monthrange(year, month)[1]
            work_days = self.get_workdays(num_days, year, month, day_to_hall_to_judge)
            quarterly_dates.extend(work_days)
            if len(quarterly_dates) >= 90:
                break

        return quarterly_dates
    '''

    @staticmethod
    def timeslot_in_first_half_of_day(time_slot):
        slots = list(TimeSlot)
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

    def isDateBetweenDates(self, date, start_date, end_date):
        datetime_date = datetime.datetime(date.year , date.month , date.day)
        return (datetime_date > start_date) and ( datetime_date < end_date)

    def get_case_id_to_judge_id(self):
        case_judge_locations = db.session.query(CaseJudgeLocation).filter(
            CaseJudgeLocation.case_id.in_([case.id for case in self.cases])).all()
        case_id_to_judge_id = defaultdict(int)
        for case_judge_location in case_judge_locations:
            case_id_to_judge_id[case_judge_location.case_id] = case_judge_location.judge_id
        return case_id_to_judge_id

    def judge_is_available(self, judge_id, date):
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

    def lawyer_is_not_booked(self, time_slot, lawyer_id_1, lawyer_id_2, date, location):
        if (lawyer_id_1 != '') and (lawyer_id_2 != ''):
            start_time, end_time = time_slot.split('-')
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_1 == lawyer_id_1,
                                                                              MeetingSchedule.start_time == start_time ,
                                                                                MeetingSchedule.date == date,
                                                                              MeetingSchedule.location == location).all()
            lawyers_2_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_2 == lawyer_id_2,
                                                                MeetingSchedule.start_time == start_time,
                                                                                MeetingSchedule.date == date,
                                                                MeetingSchedule.location == location).all()
            return (len(lawyers_1_cases_that_day) == 0) and (len(lawyers_2_cases_that_day) == 0)
        if (lawyer_id_1 != '') and (lawyer_id_2 == ''):
            start_time, end_time = time_slot.split('-')
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_1 == lawyer_id_1,
                                                                              MeetingSchedule.start_time == start_time ,
                                                                                MeetingSchedule.date == date,
                                                                              MeetingSchedule.location == location).all()
            return (len(lawyers_1_cases_that_day) == 0)
        if  (lawyer_id_2 != '') and (lawyer_id_1 == '') :
            start_time, end_time = time_slot.split('-')
            lawyers_1_cases_that_day = db.session.query(MeetingSchedule).filter(MeetingSchedule.lawyer_id_2 == lawyer_id_2,
                                                                              MeetingSchedule.start_time == start_time ,
                                                                                MeetingSchedule.date == date,
                                                                              MeetingSchedule.location == location).all()
            return (len(lawyers_1_cases_that_day) == 0)
        return True

    def date_relevant_for_case(self, j_date, judge_id, case, location):
        '''
        input - date, judge_id

        checks if judge of case is working on this date and returns True if yes False if no
        '''
        for hall_number, time_slot_dict in j_date.schedule.items():
            for time_slot, judge_dict in time_slot_dict.items():
                lawyers_available = (
                    self.lawyer_is_not_booked(time_slot, case.lawyer_id_1, case.lawyer_id_2, j_date.date,  location))
                if lawyers_available:
                    for judge, case_id in judge_dict.items():
                        if judge_id == judge and self.judge_is_available(judge_id, j_date.date):
                            if case_id == '':
                                return True, hall_number, time_slot
        return False, False, False

    def add_meeting_to_schedule(self, case, date, time_slot, hall_number, judge_id, lawyer_id_1, lawyer_id_2
                                , meeting_location):
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
                                     lawyer_id_2=lawyer_id_2,
                                     location=meeting_location)
        add_to_db(meeting_schedule)


class JerusalemScheduler(LocationScheduler):
    def __init__(self, cases):
        self.location = 'Jerusalem'
        LocationScheduler.__init__(self, cases, self.location)
        self.halls = self.get_halls(self.location)

    def schedule_cases(self):
        '''
        MAIN FUNCTION
        :return:
        '''
        ordered_cases = self.order_cases()
        case_id_to_judge_id = self.get_case_id_to_judge_id()
        quarterly_dates = self.get_next_90_dates(DayToHallToJudgeJerusalem)
        quarterly_j_days = [Day(date, DayToHallToJudgeJerusalem) for date in quarterly_dates]
        # case object
        i = 1
        for case in ordered_cases:
            print('Starting Jerusalem case {} / {} scheduling'.format(i, len(ordered_cases)))

            judge_id = case_id_to_judge_id[case.id]
            been_placed_in_calendar = False
            for J_date in quarterly_j_days:
                if been_placed_in_calendar:
                    break
                lawyers_available = self.lawyer_is_not_in_different_city(J_date.date, case.lawyer_id_1, case.lawyer_id_2, 'Jerusalem')
                if lawyers_available:
                    relevant, hall_number, time_slot = self.date_relevant_for_case(J_date, judge_id, case, 'Jerusalem')
                    if relevant:
                        print('Done - Found! Jerusalem case relevancy {} / {}'.format(i, len(ordered_cases)))
                        been_placed_in_calendar = True
                        J_date.schedule[hall_number][time_slot][judge_id] = case.id
                        print('Adding Jerusalem case  {} / {} to DB'.format(i, len(ordered_cases)))
                        self.add_meeting_to_schedule(case, J_date.date, time_slot, hall_number,
                                                     case_id_to_judge_id[case.id],case.lawyer_id_1 , case.lawyer_id_2,
                                                     'Jerusalem')
                        print('Done - Adding Jerusalem case  {} / {} to DB'.format(i, len(ordered_cases)))

            if not been_placed_in_calendar:
                print('Case {} has not been placed in calendar!'.format(case.id))
            print('Done - Jerusalem case {} / {} scheduling'.format(i, len(ordered_cases)))
            i += 1


class TelAvivScheduler(LocationScheduler):
    def __init__(self, cases):
        self.location = 'Tel Aviv'
        LocationScheduler.__init__(self, cases, self.location)
        self.halls = self.get_halls(self.location)

    def schedule_cases(self):
        '''
        MAIN FUNCTION
        :return:
        '''
        ordered_cases = self.order_cases()
        case_id_to_judge_id = self.get_case_id_to_judge_id()
        quarterly_dates = self.get_next_90_dates(DayToHallToJudgeTelAviv)
        quarterly_t_a_days = [Day(date, DayToHallToJudgeTelAviv) for date in quarterly_dates]
        # case object
        i = 1
        for case in ordered_cases:
            # TODO: for debug remove later
            if case.id == '2302-22':
                print('got here')

            ##############
            print('Starting Tel Aviv case {} / {} scheduling'.format(i, len(ordered_cases)))

            judge_id = case_id_to_judge_id[case.id]
            been_placed_in_calendar = False
            for T_date in quarterly_t_a_days:
                if been_placed_in_calendar:
                    break
                lawyers_available = self.lawyer_is_not_in_different_city(T_date.date, case.lawyer_id_1, case.lawyer_id_2
                                                                         , 'Tel Aviv')
                if lawyers_available:
                    relevant, hall_number, time_slot = self.date_relevant_for_case(T_date, judge_id ,case, 'Tel Aviv')
                    if relevant:
                        print('Done - Found! Tel Aviv case relevancy {} / {}'.format(i, len(ordered_cases)))
                        been_placed_in_calendar = True
                        T_date.schedule[hall_number][time_slot][judge_id] = case.id
                        print('Adding Tel Aviv case  {} / {} to DB'.format(i, len(ordered_cases)))
                        self.add_meeting_to_schedule(case, T_date.date, time_slot, hall_number,
                                                     case_id_to_judge_id[case.id],case.lawyer_id_1, case.lawyer_id_2
                                                     , 'Tel Aviv')
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
        #j_scheduler = JerusalemScheduler(self.location_to_cases['ירושלים'])
        print('Done - Getting Jerusalem cases')
        #j_scheduler.schedule_cases()

        t_scheduler = TelAvivScheduler(self.location_to_cases['תל אביב'])
        t_scheduler.schedule_cases()

