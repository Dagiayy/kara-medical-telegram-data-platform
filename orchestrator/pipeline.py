# orchestrator/pipeline.py
import subprocess

from dagster import Failure, OpExecutionContext, job, op


def _run(context: OpExecutionContext, cmd: list) -> None:
    context.log.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Failure(description=f"Command failed ({result.returncode}): {' '.join(cmd)}")


@op
def scrape_telegram_data(context: OpExecutionContext):
    # Requires TELEGRAM_SESSION_STRING in the environment -- this step runs
    # unattended and cannot answer an interactive phone-number prompt.
    _run(context, ["python", "-m", "app.scraper.scrape_telegram"])


@op
def load_raw_to_postgres(context: OpExecutionContext, start_after):
    _run(context, ["python", "-m", "app.scraper.load_raw_to_pg"])


@op
def run_yolo_enrichment(context: OpExecutionContext, start_after):
    _run(context, ["python", "-m", "kara_detection.detect_images"])


@op
def run_dbt_seed(context: OpExecutionContext, start_after):
    _run(context, ["dbt", "seed", "--project-dir", "kara_dbt"])


@op
def run_dbt_transformations(context: OpExecutionContext, start_after):
    _run(context, ["dbt", "run", "--project-dir", "kara_dbt"])


@op
def run_dbt_tests(context: OpExecutionContext, start_after):
    _run(context, ["dbt", "test", "--project-dir", "kara_dbt"])


@job
def kara_pipeline():
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(start_after=scraped)
    detected = run_yolo_enrichment(start_after=loaded)
    seeded = run_dbt_seed(start_after=detected)
    transformed = run_dbt_transformations(start_after=seeded)
    run_dbt_tests(start_after=transformed)
