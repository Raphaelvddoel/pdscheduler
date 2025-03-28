import time
from typing import List
import datetime
import csv

from pdscheduler.pager_duty_user import PagerDutyUser


class ScheduleCreator:

    def __init__(
        self,
        name: str,
        description: str,
        days: List[str],
        timezone: str,
        start_hour: int,
        end_hour: int,
        users: List[PagerDutyUser],
        file_path: str,
    ):

        self.name = name
        self.description = description
        self.days = days
        self.timezone = timezone
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.users = users
        self.file_path = file_path

        self.schedule = {}

    def validate(self):
        if not self.name:
            raise ValueError("Schedule name is required.")
        if not self.description:
            raise ValueError("Schedule description is required.")
        if not self.days:
            raise ValueError("Days of the week are required.")
        if not self.timezone:
            raise ValueError("Timezone is required.")
        if not self.start_hour or not self.end_hour:
            raise ValueError("Start and end hours are required.")
        if not self.users:
            raise ValueError("Users are required.")
        if not self.file_path:
            raise ValueError("CSV file path is required.")

        self._validate_csv_file()

    def _validate_csv_file(self):
        try:
            with open(self.file_path, "r") as file:
                csv_reader = csv.reader(file)
                # Check if the first row is a header
                header = next(csv_reader)
                if header != ["user_email", "week_day", "start_time", "end_time"]:
                    raise ValueError(
                        "CSV file must have the following headers: Email, Weekday, Start Time, End Time"
                    )
        except FileNotFoundError:
            raise ValueError(f"CSV file not found at {self.file_path}")
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")

    def generate_data(self):
        self._set_general_data()
        self._generate_layers()
        self.generate_restrictions()

        return self.schedule

    def _set_general_data(self):
        self.schedule = {
            "name": self.name,
            "time_zone": self.timezone,
            "description": self.description,
            "schedule_layers": [],
        }

    def _generate_layers(self):
        self.schedule["schedule_layers"] = [
            {
                "name": f"Layer for {user.name}",
                "start": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                "end": (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(weeks=1)
                ).strftime("%Y-%m-%dT%H:%M:%S"),
                "rotation_virtual_start": time.strftime(
                    "%Y-%m-%dT%H:%M:%S", time.gmtime()
                ),
                "users": [{"user": {"id": user.id, "type": "user"}}],
                "rotation_turn_length_seconds": 3600,  # one hour
                "restrictions": [],
            }
            for user in self.users
        ]

    def generate_restrictions(self):
        with open(self.file_path, "r") as file:
            csv_reader = csv.reader(file)
            # Skip the header (first row)
            next(csv_reader)

            for row in csv_reader:
                user = self._get_user_by_email(row[0])
                self._add_restriction(user, row[1], row[2], row[3])

    def _add_restriction(
        self, user: PagerDutyUser, weekday: str, start_time: str, end_time: str
    ):
        # Find schedule belonging to user
        for layer in self.schedule["schedule_layers"]:
            if layer["users"][0]["user"]["id"] == user.id:
                # Add restriction to the user's schedule layer
                restriction = {
                    "type": "weekly_restriction",
                    "start_day_of_week": time.strptime(
                        weekday.capitalize(), "%A"
                    ).tm_wday
                    + 1,  # Convert weekday to 1-7 (Monday-Sunday)
                    "start_time_of_day": f"{start_time}:00",
                    "duration_seconds": (
                        datetime.datetime.strptime(end_time, "%H:%M")
                        - datetime.datetime.strptime(start_time, "%H:%M")
                    ).seconds,
                }
                layer["restrictions"].append(restriction)
                break

    def _get_user_by_email(self, email: str) -> PagerDutyUser:
        for user in self.users:
            if user.email == email:
                return user

        return None

    def _get_remaining_users(self, user: PagerDutyUser) -> List[PagerDutyUser]:
        return [u for u in self.users if u != user]
