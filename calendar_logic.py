from __future__ import annotations
from enum import Enum
from datetime import datetime, date, timedelta

from loguru import logger


class DayType(Enum):
    WORKDAY = 0
    HOLIDAY = 1


class Day:
    def __init__(self, timestamp: datetime, is_issue_day: bool) -> Day:
        self.is_issue_day = is_issue_day
        self.day_type = (
            DayType.HOLIDAY
            if HolidayCalendar.is_holiday(timestamp.date())
            else DayType.WORKDAY
        )
        self.open = Hours.opening_hours[self.day_type]
        self.close = Hours.closing_hours[self.day_type]
        self.timestamp = timestamp

    def __sub__(self, other):
        if not isinstance(other, Day):
            raise ValueError("Day can only be subtracted with Day.")
        if self.timestamp.date() == other.timestamp.date():
            return self.timestamp - other.timestamp
        multiplicator = 1
        if self.timestamp < other.timestamp:
            logger.debug("Negative time difference has been found.")
            minuend = other.timestamp
            sub = self.timestamp
            multiplicator = -1
        else:
            minuend = self.timestamp
            sub = other.timestamp

        delta = minuend.date() - sub.date()
        seconds_sum = 0
        for i in range(delta.days + 1):
            day = sub.date() + timedelta(days=i)
            seconds_sum += HolidayCalendar.get_seconds(day)
        minuend_close = Hours.get_close(minuend)
        logger.info(
            f"Trying to subtract {minuend.replace(hour=minuend_close.hour, minute=minuend_close.minute, second=minuend_close.second)} - {minuend}"
        )
        seconds_sum -= (
            minuend.replace(
                hour=minuend_close.hour,
                minute=minuend_close.minute,
                second=minuend_close.second,
            )
            - minuend
        ).total_seconds()
        sub_open = Hours.get_open(sub)
        seconds_sum -= (
            sub
            - sub.replace(
                hour=sub_open.hour, minute=sub_open.minute, second=sub_open.second
            )
        ).total_seconds()
        logger.info(f"Minuend: {minuend} Subtrahent: {sub}, seconds_sum: {seconds_sum}")
        td = timedelta(seconds=(seconds_sum * multiplicator))
        logger.debug(
            f"Hours: {td.days*24 + td.seconds//3600} Minutes: {(td.seconds//60)%60} Seconds: {td.seconds%60}"
        )
        return td

    def __repr__(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def from_timestamp(cls, timestamp: datetime, issue_not_resolve: bool) -> Day:
        day = Day(timestamp=timestamp, is_issue_day=issue_not_resolve)
        if cls.is_time_between(day.open, day.close, timestamp.time()):
            return day
        if timestamp.time() > day.close:
            if not day.is_issue_day:
                day.timestamp = day.timestamp.replace(
                    hour=day.close.hour,
                    minute=day.close.minute,
                    second=day.close.second,
                )
            else:
                tomorrow = (day.timestamp + timedelta(days=1)).date()
                tomorrow_is_holiday = HolidayCalendar.is_holiday(tomorrow)
                next_day_type = (
                    DayType.HOLIDAY if tomorrow_is_holiday else DayType.WORKDAY
                )

                day.timestamp = day.timestamp.replace(
                    hour=Hours.opening_hours[next_day_type].hour,
                    minute=Hours.opening_hours[next_day_type].minute,
                    second=Hours.opening_hours[next_day_type].second,
                )
                day.timestamp += timedelta(days=1)
        else:
            if day.is_issue_day:
                day.timestamp = day.timestamp.replace(
                    hour=day.open.hour, minute=day.open.minute, second=day.open.second
                )
            else:
                yesterday = day.timestamp.date() - timedelta(days=1)
                yesterday_is_holiday = HolidayCalendar.is_holiday(yesterday)
                last_day_type = (
                    DayType.HOLIDAY if yesterday_is_holiday else DayType.WORKDAY
                )

                day.timestamp = day.timestamp.replace(
                    hour=Hours.closing_hours[last_day_type].hour,
                    minute=Hours.closing_hours[last_day_type].minute,
                    second=Hours.closing_hours[last_day_type].second,
                )
                day.timestamp -= timedelta(days=1)
        return day

    @staticmethod
    def is_time_between(begin_time, end_time, check_time=None):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.utcnow().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time


class Hours:
    @classmethod
    def get_open(cls, d: date):
        is_holiday = HolidayCalendar.is_holiday(d)
        day_type = DayType.HOLIDAY if is_holiday else DayType.WORKDAY
        return cls.opening_hours[day_type]

    @classmethod
    def get_close(cls, d: date):
        is_holiday = HolidayCalendar.is_holiday(d)
        day_type = DayType.HOLIDAY if is_holiday else DayType.WORKDAY
        return cls.closing_hours[day_type]

    opening_hours = {
        DayType.WORKDAY: datetime(2000, 1, 1, 6).time(),
        DayType.HOLIDAY: datetime(2000, 1, 1, 7).time(),
    }
    closing_hours = {
        DayType.WORKDAY: datetime(2000, 1, 1, 20).time(),
        DayType.HOLIDAY: datetime(2000, 1, 1, 18).time(),
    }


class HolidayCalendar:
    HOLIDAYS = [date(2021, 5, 5)]

    @classmethod
    def is_holiday(cls, current_date: date) -> bool:
        if current_date in cls.HOLIDAYS or current_date.isoweekday() > 5:
            return True
        return False

    @classmethod
    def get_seconds(cls, current_date: date) -> float:
        is_holiday = cls.is_holiday(current_date)
        day_type = DayType.HOLIDAY if is_holiday else DayType.WORKDAY
        logger.info(
            f"Date: {current_date} Trying to subtract {Hours.closing_hours[day_type]} - {Hours.opening_hours[day_type]}"
        )
        closing_time = (
            datetime.combine(date.min, Hours.closing_hours[day_type]) - datetime.min
        )
        opening_time = (
            datetime.combine(date.min, Hours.opening_hours[day_type]) - datetime.min
        )
        return (closing_time - opening_time).total_seconds()


if __name__ == "__main__":
    issue_day = Day.from_timestamp(
        datetime(2021, 3, 2, 19, 50), issue_not_resolve=True
    )  # Subtract current - open
    resolve_day = Day.from_timestamp(
        datetime(2021, 3, 6, 19, 20), issue_not_resolve=False
    )  # Subtract close - current
    timediff = resolve_day - issue_day
    print(timediff)
    exit()

    print(timediff)
    print(issue_day)
    print(resolve_day)
    exit()
    x = Day.from_timestamp(datetime(2021, 1, 1, 1, 50), issue_not_resolve=True)
    print(Day.from_timestamp)
    print(x.timestamp)
    print(x.close)
    print(type(x.close))
