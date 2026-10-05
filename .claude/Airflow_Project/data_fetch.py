from datetime import datetime
from airflow.sdk.definitions.asset import Asset
from airflow.decorators import dag, task
import json
import os

# Define the Asset globally so it can be imported or referenced
weather_data_asset = Asset(uri="file:///opt/airflow/data/weather_report.json")

@dag
def data_fetch():

    @task
    def prepare_storage():
        os.makedirs("/opt/airflow/data", exist_ok=True)
        return "/opt/airflow/data/weather_report.json"

    @task
    def fetch_api_data():
        # Simulating an API call
        return {"city": "New York", "temp": 22, "unit": "C"}

    @task
    def transform_data(raw_data):
        # Professional touch: add metadata/processing info
        raw_data["processed_at"] = datetime.now().isoformat()
        raw_data["status"] = "cleansed"
        return raw_data

    @task(outlets=[weather_data_asset]) # <--- This is where the magic happens
    def materialize_asset(final_data, path):
        with open(path, "w") as f:
            json.dump(final_data, f)
        print(f"Asset materialized at {path}")

    # Set up the professional dependency chain
    storage_path = prepare_storage()
    raw = fetch_api_data()
    clean = transform_data(raw)
    materialize_asset(clean, storage_path)

data_fetch()