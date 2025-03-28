import json
from typing import List, Optional

import requests

from pdpyras import APISession, PDClientError

BASE_URL = "https://api.pagerduty.com"


class PDSchedulingException(Exception):
    def __init__(self, message, extra_info=None):
        super().__init__(message)
        self.extra_info = extra_info


class PDSchedulingNetworkException(PDSchedulingException):
    status_code = None
    reason = ""

    def __init__(
        self,
        message,
        status_code: Optional[int] = None,
        reason: Optional[str] = None,
        extra_info: Optional[str] = None,
    ):
        self.status_code = status_code
        self.reason = reason or "Unknown"
        self.extra_info = extra_info

        super().__init__(message, extra_info=extra_info)


def _create_scheduling_exception(result):
    if result is None:
        message = "PagerDuty request failed with unknown status code"
        extra_info = "No result returned from the request."
    else:
        result_json = result.json() if hasattr(result, "json") else {}

        # Handle error if present
        error_code = result_json.get("error", {}).get("code", "N/A")
        error_message = result_json.get("error", {}).get("message", "N/A")
        error_details = result_json.get("error", {}).get("errors", {})

        message = f"PagerDuty request failed: {result.reason}"
        extra_info = f"Error Code: {error_code}, Message: {error_message}, Details: {error_details}"

    return PDSchedulingNetworkException(
        message=f"{message}. Additional Info: {extra_info}",
        status_code=None if result is None else result.status_code,
        reason=None if result is None else result.reason,
        extra_info=extra_info,
    )


class PagerDuty:
    def __init__(self, token):
        self.token = token

    def headers(self):
        return {
            "content-type": "application/json",
            "Authorization": f"Token token={self.token}",
            "Accept": "application/vnd.pagerduty+json;version=2",
        }

    def get_users(self, teams: Optional[List[str]] = None):
        """Fetches all users

        :return: A list of users
        """

        # TODO: add support for pagination
        session = APISession(self.token)
        try:
            params = {"include[]": "teams"}
            if teams:
                params["team_ids[]"] = ",".join(teams)
            users = list(session.iter_all("users", params=params))
        except PDClientError as e:
            raise _create_scheduling_exception(e.response) from e
        return users

    def schedules(self, query=""):
        """Fetches all schedules by default or some specific by name

        :param query: Use query to fetch specific schedule
        :return: A list of schedules
        """
        # TODO: add support for pagination
        result = None
        try:
            result = requests.get(
                url=f"{BASE_URL}/schedules?limit=100&query={query}",
                headers=self.headers(),
            )
            result.raise_for_status()
        except requests.RequestException as e:
            raise _create_scheduling_exception(result) from e
        return result.json()["schedules"]

    def get_schedule(self, *, schedule_id):
        """Fetches specific schedule by id

        :param schedule_id:
        :return: A schedule
        """
        result = None
        try:
            result = requests.get(
                url=f"{BASE_URL}/schedules/{schedule_id}",
                headers=self.headers(),
            )
            result.raise_for_status()
        except requests.RequestException as e:
            raise _create_scheduling_exception(result) from e
        return result.json()

    def create_schedule(self, *, data: dict):
        result = None
        try:
            result = requests.post(
                url=f"{BASE_URL}/schedules",
                headers=self.headers(),
                data=json.dumps(data),
            )
            result.raise_for_status()
        except requests.RequestException as e:
            raise _create_scheduling_exception(result) from e
        return result

    def update_schedule(self, *, schedule_id: str, data: dict):
        """Updates existing schedule in place

        :param schedule_id: A schedule id
        :param name: A name which will be assigned to schedule
        :param hours: A list of size 24*7 with each entry a user id assigned for the hour
        :return: Updated schedule
        """
        current_schedule = self.get_schedule(schedule_id=schedule_id)

        for current_layer in current_schedule["schedule"]["schedule_layers"]:
            for layer in data['schedule_layers']:
                if current_layer["name"] == layer["name"]:
                    layer["id"] = current_layer["id"]
                    break

        data["id"] = schedule_id

        result = None
        try:
            result = requests.put(
                url=f"{BASE_URL}/schedules/{schedule_id}",
                headers=self.headers(),
                data=json.dumps(data),
            )
            result.raise_for_status()
        except requests.RequestException as e:
            raise _create_scheduling_exception(result) from e
        return result

    def create_or_update_schedule(self, *, data: dict):
        """Creates or updates a schedule with specific name and assignments users based on hours array

        :param name: A schedule name
        """

        name = data["name"]
        schedules = self.schedules(query=name)
        if schedules:
            assert len(schedules) == 1
            return self.update_schedule(schedule_id=schedules[0]["id"], data=data)
        else:
            return self.create_schedule(data=data)
