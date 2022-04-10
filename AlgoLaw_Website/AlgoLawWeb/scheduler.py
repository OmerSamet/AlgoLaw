from collections import defaultdict
from AlgoLawWeb.models import Hall, Case, CaseJudgeLocation, MeetingSchedule, Meeting, Vacation, Rotation, SickDay
import datetime, calendar
import enum
from AlgoLawWeb import db
from AlgoLawWeb.utilities import add_to_db


class JerusalemTimeSlots(enum.Enum):
    nine_to_nine_thirty_five = '09:00-09:35'
    nine_forty_five_to_ten_twenty = '09:45-10:20'
    ten_thirty_to_eleven_o_five = '10:30-11:05'
    eleven_fifteen_to_eleven_fifty = '11:15-11:50'
    twelve_to_twelve_thirty_five = '12:00-12:35'
    twelve_forty_five_to_one_twenty = '12:45-13:20'
    one_thirty_to_two_o_five = '13:30-14:05'
    two_fifteen_to_two_fifty = '14:15-14:50'


#  {daynum: {hall_number: [judge1, judge2]
DayToHallToJudge = {
    7: {1: [1, 1], 2: [2, 2], 3: [9, 10]},  # Sunday
    1: {1: [3, 3], 2: [4, 4], 3: [7, 8]},  # Monday
    2: {1: [5, 5], 2: [6, 6], 3: [0, 2]},  # Tuesday
    3: {1: [7, 7], 2: [8, 8], 3: [3, 4]},  # Wednesday
    4: {1: [9, 9], 2: [10, 10], 3: [5, 6]}  # Thursday
}


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
            if day_date.isoweekday() in DayToHallToJudge.keys():
                work_days.append(day_date)
        return work_days

    def get_quarterly_dates(self):
        year = datetime.datetime.now().year
        quarterly_dates = []
        for i in range(0, 3):
            month = datetime.datetime.now().month + i
            num_days = calendar.monthrange(year, month)[1]
            work_days = self.get_workdays(num_days, year, month)
            quarterly_dates.extend(work_days)

        return quarterly_dates

    @staticmethod
    def get_timeslot_dict(halls):
        '''
        :input: halls -> list of hall objects
        {time_slot: {hall_id: case_id,
                    hall_id: case_id
                    hall_id: case_id
        '''
        timeslot_dict = defaultdict(lambda: defaultdict(Case))
        for timeslot in JerusalemTimeSlots:
            for hall in halls:
                timeslot_dict[timeslot][hall.hall_number] = None

        return timeslot_dict
    #
    #             {JerusalemTimeSlots.nine_to_nine_thirty_five: 0,
    #                         JerusalemTimeSlots.nine_forty_five_to_ten_twenty: 0,
    #                         JerusalemTimeSlots.ten_thirty_to_eleven_o_five: 0,
    #                         JerusalemTimeSlots.eleven_fifteen_to_eleven_fifty: 0,
    #                         JerusalemTimeSlots.twelve_to_twelve_thirty_five: 0,
    #                         JerusalemTimeSlots.twelve_forty_five_to_one_twenty: 0,
    #                         JerusalemTimeSlots.one_thirty_to_two_o_five: 0,
    #                         JerusalemTimeSlots.two_fifteen_to_two_fifty: 0
    # }

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
        quarterly_dates = self.get_quarterly_dates()
        jerusalem_empty_timeslot_dict = self.get_timeslot_dict(halls)
        empty_schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(datetime.date))))
        for date in quarterly_dates:
            empty_schedule[date] = jerusalem_empty_timeslot_dict

        return empty_schedule


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
            return judge_id == DayToHallToJudge[day_of_week][hall_number][0]
        else:
            return judge_id == DayToHallToJudge[day_of_week][hall_number][1]


    def isDateBetweenDates(self ,date, startDate, endDate):
        datetime_date = datetime.datetime(date.year , date.month , date.day)
        return (datetime_date > startDate) and ( datetime_date < endDate)

    def judgeIsAvailable(self, judge_id , date):
        vacations = db.session.query(Vacation).filter(Vacation.is_verified).all()
        for vac in vacations:
            if vac.judge_id == judge_id & self.isDateBetweenDates(date , vac.start_date , vac.end_date):
                return False

        sick_days = db.session.query(SickDay).filter(SickDay.is_verified).all()
        for sick_day in sick_days:
            if sick_day.judge_id == judge_id & self.isDateBetweenDates(date, sick_day.start_date, sick_day.end_date):
                return False

        rotations = db.session.query(Rotation).filter(SickDay.is_verified).all()
        for rot in rotations:
            if rot.judge_id == judge_id & self.isDateBetweenDates(date, rot.start_date, rot.end_date):
                return False

        return True

    def add_meeting_to_schedule(self, case, date, time_slot, hall_number, judge_id):
        self.hall_schedules[date][time_slot][hall_number] = case
        start_time, end_time = time_slot.value.split('-')
        # add meeting to DB
        quarter = ((date.month - 1) // 3) + 1
        meeting = Meeting(case_id=case.id,
                          quarter=quarter,
                          year=date.year)
        add_to_db(meeting)
        meeting_id = Meeting.query.filter(Meeting.case_id == case.id,
                                          Meeting.quarter == quarter,
                                          Meeting.year == date.year).first().id
        # get hall id from hall number
        hall = Hall.query.filter(Hall.location == case.location,
                                 Hall.hall_number == hall_number).first()

        # add meeting scheduling
        meeting_schedule = MeetingSchedule(case_id=case.id,
                                     hall_id=hall.id,
                                     date=date,
                                     judge_id=judge_id,
                                     start_time=start_time,
                                     end_time=end_time,
                                     meeting_id=meeting_id)
        add_to_db(meeting_schedule)

    def get_case_id_to_judge_id(self):
        case_judge_locations = db.session.query(CaseJudgeLocation).filter(
            CaseJudgeLocation.case_id.in_([case.id for case in self.cases])).all()
        case_id_to_judge_id = defaultdict(int)
        for case_judge_location in case_judge_locations:
            case_id_to_judge_id[case_judge_location.case_id] = case_judge_location.judge_id
        return case_id_to_judge_id

    def schedule_cases(self):
        '''
        MAIN FUNCTION
        :return:
        '''
        ordered_cases = self.order_cases()
        case_id_to_judge_to_location = self.get_case_id_to_judge_id()
        # case object
        for case in ordered_cases:
            # datetime, dict -> {timeslot: {hall_number: case object ...
            for date, time_slot_dict in self.hall_schedules.items():
                # timeslot  ,dict -> {hall_number: case object ...
                for time_slot, hall_dict in time_slot_dict.items():
                    # hall_number, case object
                    for hall_number, scheduled_case in hall_dict.items():
                        if not scheduled_case:  # means there is no case there
                            # check if at this time the relevant judge is working
                            if (self.relevant_judge(case_id_to_judge_to_location[case.id], date, hall_number, time_slot)) and (self.judgeIsAvailable(case_id_to_judge_to_location[case.id],date)):
                                self.add_meeting_to_schedule(case, date, time_slot, hall_number, case_id_to_judge_to_location[case.id])


class MeetingScheduler:
    def __init__(self, start_date):
        self.start_date = start_date  # start of quarter
        self.quarter = ((start_date.month - 1) // 3) + 1
        self.output_path = r'/Users/omersamet/Documents/Personal Docs/Google/AlgoLaw/AlgoLaw_Website/output.csv'
        self.year = start_date.year
        self.location_to_cases = self.divide_cases_to_location()  # dict { 'location': [cases] ...

    def get_uploaded_cases(self):
        '''
        using self.quarter loads relevant cases
        :return: cases -> list of Case objects (AlgoLawWeb.models.Case)
        '''

        case_judge_locations = db.session.query(CaseJudgeLocation).filter(
            CaseJudgeLocation.quarter == self.quarter,
            CaseJudgeLocation.year == self.year).all()

        case_ids = [cjl.case_id for cjl in case_judge_locations]

        cases = db.session.query(Case).filter(Case.id.in_(case_ids)).all()

        return cases

    def divide_cases_to_location(self):
        cases = self.get_uploaded_cases()
        location_to_cases = defaultdict(list)  # dict of location to case list -> {location_name_str: [Case], ...
        for case in cases:
            location_to_cases[case.location].append(case)

        return location_to_cases

    def schedule_jerusalem_cases(self):
        j_scheduler = JerusalemScheduler(self.location_to_cases['Jerusalem'])
        j_scheduler.schedule_cases()
