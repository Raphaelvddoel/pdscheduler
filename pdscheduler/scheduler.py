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

    def set_name(self, name: str) -> None:
        """
        Set the name of the schedule.

        Args:
            name (str): The name to set for the schedule.

        Returns:
            None
        """
        self.name = name

    def set_description(self, description: str) -> None:
        """
        Set the description of the schedule.

        Args:
            description (str): The description to set for the schedule.

        Returns:
            None
        """
        self.description = description

    def set_users_from_pager_duty(self, teams: Optional[List[str]] = None) -> None:
        """
        Fetch users from PagerDuty and store them in the scheduler.

        Args:
            teams (Optional[List[str]]): A list of team IDs to filter users by. If None, fetches all users.

        Returns:
            None
        """
        self.users = [PagerDutyUser(user) for user in self.pager_duty.get_users(teams)]

    def get_users(self) -> List[PagerDutyUser]:
        """
        Get a list of users in the scheduler.

        Returns:
            List[PagerDutyUser]: A copy of the list of users.
        """
        return self.users.copy()

    def select_users_for_schedule(self, user_ids: Union[str, List[str]]) -> None:
        """
        Filter the users list to only include the specified user IDs.

        Args:
            user_ids (Union[str, List[str]]): A single user ID or a list of user IDs to include in the schedule.

        Returns:
            None
        """

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        self.users = [user for user in self.users if user.id in user_ids]

    def exclude_users_from_schedule(self, user_ids: Union[str, List[str]]) -> None:
        """
        Remove the specified users from the schedule.

        Args:
            user_ids (Union[str, List[str]]): A single user ID or a list of user IDs to exclude from the schedule.

        Returns:
            None
        """

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        self.users = [user for user in self.users if user.id not in user_ids]

    def set_days_of_week(self, days: List[str]) -> None:
        """
        Set the days of the week for the schedule, ensuring they are valid.

        Args:
            days (List[str]): A list of day names to set for the schedule.

        Raises:
            ValueError: If any provided day is not a valid weekday.

        Returns:
            None
        """

        lower_days = [day.lower() for day in days]

        invalid_days = [day for day in lower_days if day not in self.VALID_DAYS]
        if invalid_days:
            raise ValueError(
                f"Invalid day(s) provided: {', '.join(invalid_days)}. Days must be valid weekdays."
            )

        self.days = lower_days

    def set_hours_of_day(self, start_hour: int, end_hour: int) -> None:
        """
        Set the hours of the day for the schedule, ensuring valid input.

        Args:
            start_hour (int): The starting hour (0-23).
            end_hour (int): The ending hour (0-23).

        Raises:
            ValueError: If the hours are not within the valid range (0-23) or if start_hour is not less than end_hour.

        Returns:
            None
        """

        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            raise ValueError("Hours must be between 0 and 23 (inclusive).")

        if start_hour >= end_hour:
            raise ValueError("Start hour must be less than end hour.")

        self.start_hour = start_hour
        self.end_hour = end_hour

    def set_timezone(self, timezone: str) -> None:
        """
        Set the timezone for the schedule, ensuring it is valid.

        Args:
            timezone (str): The timezone string (e.g., "America/New_York").

        Raises:
            ValueError: If the provided timezone is not recognized.

        Returns:
            None
        """

        try:
            # Attempt to get the timezone to validate it
            pytz.timezone(timezone)
            self.timezone = timezone
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone}")

    def set_csv_file_location(self, file_path: str):
        """
        Set the file path for the CSV file.

        Args:
            file_path (str): The path to the CSV file.

        Returns:
            None
        """

        self.file_path = file_path

    def generate_schedule(self):
        """
        Generate a schedule for the week based on user availability.

        This method creates a schedule using the current settings (name, description,
        days, timezone, hours, users, and file path) and stores the generated schedule.

        Returns:
            None
        """

        generator = ScheduleCreator(
            self.name,
            self.description,
            self.days,
            self.timezone,
            self.start_hour,
            self.end_hour,
            self.users,
            self.file_path,
        )

        self.schedule = generator.generate_data()

    def _handle_schedule_response(self, result) -> None:
        """
        Handle the response after creating or updating a schedule.

        This method checks if the response is valid and contains schedule data.
        If the response is valid, it prints the schedule's ID, name, and URL.
        If the response is invalid or missing data, it raises a ValueError.

        Args:
            result: The response object containing the result of the schedule creation or update.

        Raises:
            ValueError: If the result is empty, doesn't contain valid schedule data, or fails to create/update the schedule.

        Returns:
            None
        """

        if not result:
            raise ValueError("Failed to create/update schedule. Please check the data.")

        result_data = result.json().get("schedule")
        if not result_data:
            raise ValueError(
                "Failed to create/update schedule. No schedule data returned."
            )

        print(
            f"Successfully created schedule. Schedule ID: {result_data['id']}, "
            f"Name: {result_data['name']}, schedule can be found on {result_data['html_url']}"
        )

    def _ensure_local_schedule_exists(self):
        if not self.schedule:
            raise ValueError(
                "Schedule not generated. Please call generate_schedule() first."
            )

    def create_schedule(self) -> None:
        """
        Creates a new schedule in PagerDuty.

        This method checks if a local schedule exists and then attempts to create
        a new schedule using the PagerDuty API.
        If the schedule creation is successful, it prints the schedule's ID, name,
        and URL. If the schedule creation fails, it raises a ValueError.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: If the schedule creation fails or if the schedule data is invalid.
            ValueError: If the schedule is not generated locally.
            PDSchedulingNetworkException: If there is an error during the API request.
        """

        self._ensure_local_schedule_exists()
        result = self.pager_duty.create_schedule(data=self.schedule)
        self._handle_schedule_response(result)

    def update_schedule(self, schedule_id: str) -> None:
        """
        Updates a schedule in PagerDuty using the provided schedule_id.

        This method checks if a local schedule exists and then attempts to update
        a schedule using the PagerDuty API.
        If the schedule creation is successful, it prints the schedule's ID, name,
        and URL. If the schedule creation fails, it raises a ValueError.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: If the schedule update fails or if the schedule data is invalid.
            ValueError: If the schedule is not generated locally.
            PDSchedulingNetworkException: If there is an error during the API request.
        """

        self._ensure_local_schedule_exists()
        result = self.pager_duty.update_schedule(
            schedule_id=schedule_id, data=self.schedule
        )
        self._handle_schedule_response(result)

    def create_or_update_schedule(self) -> None:
        """
        Creates or updates schedule in PagerDuty.

        This method checks if a local schedule exists and then checks if a schedule
        with the provided schedule name exists in PagerDuty.
        if it exists, it updates the schedule using the PagerDuty API.
        If it doesn't exist, it creates a new schedule using the PagerDuty API.
        If the schedule creation is successful, it prints the schedule's ID, name,
        and URL. If the schedule creation fails, it raises a ValueError.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: If the schedule creation fails or if the schedule data is invalid.
            ValueError: If the schedule is not generated locally.
            PDSchedulingNetworkException: If there is an error during the API request.
        """

        self._ensure_local_schedule_exists()
        result = self.pager_duty.create_or_update_schedule(data=self.schedule)
        self._handle_schedule_response(result)
