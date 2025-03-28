# PDscheduler
Automatically schedule and upload on-call rotations to PagerDuty from a CSV file.

## Overview
`PDscheduler` is a Python library designed to simplify the process of generating and uploading on-call schedules to PagerDuty. By providing a CSV file with your team's rotation details, the package will automatically create or update the schedule for the upcoming week.

### Why only one week?
Due to limitations in the PagerDuty scheduling API, the schedule can only accommodate weekdays (e.g., "Wednesday"). This means that if you are available on a Wednesday this week but not on the same weekday next week, the API will not be able to handle that variation. As a result, the tool supports generating a schedule for only the next week.


## Installation

### Method 1: pip
*Still has to be implemented*
### Method 2: Clone the repo
```bash
git clone https://github.com/Raphaelvddoel/pdscheduler.git
cd pdscheduler
pip install -r requirements
```

## Usage
### Step 1: Generate csv file
Generate a csv file with the following structure
```csv
user_email,week_day,start_time,end_time
```

- **user_email**: The email address of the team member.
- **week_day**: The day of the week (e.g., monday, tuesday, etc.).
- **start_time**: The start time of the on-call shift (in 24-hour format, e.g., `14:00`).
- **end_time**: The end time of the on-call shift (in 24-hour format, e.g., `22:00`).

#### Example csv
```csv
user_email,week_day,start_time,end_time
john.doe@example.com,monday,00:00,08:00
jane.smith@example.com,monday,08:00,16:00
alex.jones@example.com,tuesday,00:00,08:00
```

### Step 2: Get PagerDuty API key
To use PDscheduler, you will need an API access key.
1. In the navbar go to 'Integrations' > 'API Access Keys'
2. Generate a new API key or use an existing one.

### Step 3: Configure and run the script
Here's an example of how to use PDscheduler
```python
from pdscheduler.scheduler import PagerDutyScheduler

# Initialize the scheduler with your PagerDuty API key
scheduler = PagerDutyScheduler("your-api-key-here")

# Set the name, description, and timezone for the schedule
scheduler.set_name("Automatic Schedule")
scheduler.set_description("This schedule is generated automatically by pdscheduler.")
scheduler.set_timezone("Europe/Amsterdam")

# Set which days of the week and hours to include in the schedule
scheduler.set_days_of_week(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
scheduler.set_hours_of_day(9, 22)

# Set the users and exclude specific users from the schedule
scheduler.set_users_from_pager_duty()
scheduler.exclude_users_from_schedule(["excluded_user_id"])

# Set the location of your CSV file
scheduler.set_csv_file_location("test_data.csv")

# Generate and upload the schedule to PagerDuty
scheduler.generate_schedule()
scheduler.create_or_update_schedule()
```

For more information see [example.py](example.py).

## License

Distributed under the MIT License. See [License](License) for more information.


## Acknowledgments

This project is based on the work done by [skrypka/pdscheduling](https://github.com/skrypka/pdscheduling).  
Thank you to the original author(s) for their contributions.