from typing import Dict, List, Optional, Set, Union

import pytz
from pdscheduler.pager_duty import PagerDuty
from pdscheduler.pager_duty_user import PagerDutyUser
from pdscheduler.schedule_creator import ScheduleCreator


class PagerDutyScheduler:
    VALID_DAYS: Set[str] = {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }

    def __init__(self, token: str):
        self.token = token
        self.pager_duty = PagerDuty(self.token)
        self.days: List[str] = []
        self.users: List[PagerDutyUser] = []
        self.start_hour: int = 0
        self.end_hour: int = 23
        self.name: str = "Automatic Schedule"
        self.description: str = (
            "This schedule is generated automatically by pdscheduler."
        )
        self.timezone: str = "UTC"
        self.schedule: Optional[Dict] = None
        self.file_path: Optional[str] = None

    def set_name(self, name: str):
        """Sets the name of the schedule."""
        self.name = name

    def set_description(self, description: str):
        """Sets the description of the schedule."""
        self.description = description

    def set_users_from_pager_duty(self, teams: Optional[List[str]] = None):
        """Fetches users from PagerDuty and stores them in the scheduler."""
        self.users = [PagerDutyUser(user) for user in self.pager_duty.get_users(teams)]

    def get_users(self) -> List[PagerDutyUser]:
        """Returns a list of users."""
        return self.users.copy()

    def select_users_for_schedule(self, user_ids: Union[str, List[str]]):
        """Filters the users list to only include selected user IDs."""

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        self.users = [user for user in self.users if user.id in user_ids]

    def exclude_users_from_schedule(self, user_ids: Union[str, List[str]]):
        """Removes specified users from the schedule."""

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        self.users = [user for user in self.users if user.id not in user_ids]

    def set_days_of_week(self, days: List[str]):
        """Sets the days of the week for the schedule, ensuring they are valid."""
        lower_days = [day.lower() for day in days]

        invalid_days = [day for day in lower_days if day not in self.VALID_DAYS]
        if invalid_days:
            raise ValueError(
                f"Invalid day(s) provided: {', '.join(invalid_days)}. Days must be valid weekdays."
            )

        self.days = lower_days

    def set_hours_of_day(self, start_hour: int, end_hour: int):
        """Sets the hours of the day for the schedule, ensuring valid input."""
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            raise ValueError("Hours must be between 0 and 23 (inclusive).")

        if start_hour >= end_hour:
            raise ValueError("Start hour must be less than end hour.")

        self.start_hour = start_hour
        self.end_hour = end_hour

    def set_timezone(self, timezone: str):
        """Sets the timezone for the schedule."""

        try:
            # Attempt to get the timezone to validate it
            pytz.timezone(timezone)
            self.timezone = timezone
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone}")

    def set_csv_file_location(self, file_path: str):
        """Sets the file path for the CSV file."""
        self.file_path = file_path

    def generate_schedule(self):
        """Generates a schedule for the week based on user availability"""
        generator = ScheduleCreator(
            self.name,
            self.description,
            self.days,
            self.timezone,
            self.start_hour,
            self.end_hour,
            self.users,
            self.file_path
        )

        self.schedule = generator.generate_data()

    def _handle_schedule_response(self, result):
        if not result:
            raise ValueError("Failed to create/update schedule. Please check the data.")

        result_data = result.json().get("schedule")
        if not result_data:
            raise ValueError("Failed to create/update schedule. No schedule data returned.")

        print(
            f"Successfully created schedule. Schedule ID: {result_data['id']}, "
            f"Name: {result_data['name']}, schedule can be found on {result_data['html_url']}"
        )

    def _ensure_schedule_exists(self):
        if not self.schedule:
            raise ValueError("Schedule not generated. Please call generate_schedule() first.")

    def create_schedule(self):
        self._ensure_schedule_exists()
        result = self.pager_duty.create_schedule(data=self.schedule)
        self._handle_schedule_response(result)

    def update_schedule(self, schedule_id: str):
        self._ensure_schedule_exists()
        result = self.pager_duty.update_schedule(schedule_id=schedule_id, data=self.schedule)
        self._handle_schedule_response(result)

    def create_or_update_schedule(self):
        self._ensure_schedule_exists()
        result = self.pager_duty.create_or_update_schedule(data=self.schedule)
        self._handle_schedule_response(result)
