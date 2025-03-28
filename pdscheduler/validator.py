import pytz

VALID_DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

def validate_days(days):
    invalid_days = [day for day in days if day.lower() not in VALID_DAYS]
    if invalid_days:
        raise ValueError(f"Invalid day(s) provided: {', '.join(invalid_days)}. Days must be valid weekdays.")

def validate_hours(start_hour, end_hour):
    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
        raise ValueError("Hours must be between 0 and 23.")
    if start_hour >= end_hour:
        raise ValueError("Start hour must be less than end hour.")

def validate_timezone(timezone):
    try:
        pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone}")
