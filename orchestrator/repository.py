# orchestrator/repository.py

from dagster import Definitions
from .pipeline import kara_pipeline
from .schedules import daily_kara_schedule

defs = Definitions(
    jobs=[kara_pipeline],
    schedules=[daily_kara_schedule]
)
