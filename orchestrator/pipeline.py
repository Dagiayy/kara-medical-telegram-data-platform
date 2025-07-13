# orchestrator/pipeline.py

from dagster import op, job
import subprocess

@op
def scrape_telegram_data():
    subprocess.run(["python", "app/scraper/scrape_telegram.py"], check=True)

@op
def load_raw_to_postgres():
    subprocess.run(["python", "app/scraper/load_raw_to_pg.py"], check=True)

@op
def run_dbt_transformations():
    subprocess.run(["dbt", "run", "--project-dir", "kara_dbt"], check=True)

@op
def run_yolo_enrichment():
    subprocess.run(["python", "kara_detection/detect_images.py"], check=True)

@job
def kara_pipeline():
    data = scrape_telegram_data()
    load = load_raw_to_postgres(start_after=data)
    transform = run_dbt_transformations(start_after=load)
    run_yolo_enrichment(start_after=transform)
