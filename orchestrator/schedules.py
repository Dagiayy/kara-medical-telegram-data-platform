# orchestrator/schedules.py

from dagster import ScheduleDefinition
from .pipeline import kara_pipeline

daily_kara_schedule = ScheduleDefinition(
    job=kara_pipeline,
    cron_schedule="0 6 * * *",  # Every day at 6:00 AM
    name="daily_kara_schedule"
)
