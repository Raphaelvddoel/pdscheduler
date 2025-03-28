from pdscheduler.scheduler import PagerDutyScheduler

scheduler = PagerDutyScheduler("your-api-key-here")

scheduler.set_name("Automatic Schedule")
scheduler.set_description("This schedule is generated automatically by pdscheduler.")
scheduler.set_timezone("Europe/Amsterdam")

scheduler.set_days_of_week(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
scheduler.set_hours_of_day(9,22)

scheduler.set_users_from_pager_duty()
scheduler.exclude_users_from_schedule(["excluded_user_id"])

scheduler.set_csv_file_location("test_data.csv")

scheduler.generate_schedule()
scheduler.create_or_update_schedule()