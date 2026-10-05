from datetime import datetime
from airflow.decorators import dag, task
from airflow.settings import json
# We import the asset object from the producer file 
# or define an identical Asset(uri=...) here.
from data_fetch import weather_data_asset 

@dag(schedule=[weather_data_asset])
def data_report():

    @task
    def read_asset():
        with open("/opt/airflow/data/weather_report.json", "r") as f:
            data = json.load(f)
            print(f"Analyzing data for {data['city']}: {data['temp']}°C")

    read_asset()

data_report()