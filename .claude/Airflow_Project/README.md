# Airflow Project - DAG Documentation

**Last Updated**: 2026-10-05 (continuously maintained)

This project contains two interdependent Apache Airflow DAGs that demonstrate a data pipeline workflow using Airflow's asset-based triggering feature.

## DAGs Overview

### 1. `data_fetch.py` - Data Fetch DAG

**Purpose**: Fetch weather data from an external API, transform it, and materialize it as an asset for downstream consumption.

**Schedule**: Runs on a default schedule (configurable).

**Tasks**:
- **prepare_storage()**: Creates the necessary storage directory (`/opt/airflow/data`) to store the weather report.
- **fetch_api_data()**: Simulates an API call to fetch weather data. Currently returns sample data with city, temperature, and unit information.
- **transform_data()**: Enriches the raw data by adding metadata:
  - `processed_at`: ISO timestamp of when the data was processed
  - `status`: Processing status (set to "cleansed")
- **materialize_asset()**: Writes the final processed data to a JSON file (`weather_report.json`) at the specified path. This task outputs the `weather_data_asset`, making it available for other DAGs to consume.

**Output Asset**: 
- `weather_data_asset`: File-based asset pointing to `/opt/airflow/data/weather_report.json`

**Data Flow**:
```
prepare_storage() → fetch_api_data() → transform_data() → materialize_asset()
```

---

### 2. `data_report.py` - Data Report DAG

**Purpose**: Consume the weather data asset produced by `data_fetch` DAG and generate analysis/reports.

**Trigger**: Automatically triggered when the `weather_data_asset` is updated by the `data_fetch` DAG (asset-based triggering).

**Tasks**:
- **read_asset()**: Reads the materialized weather data from the JSON file and performs analysis:
  - Extracts city and temperature information
  - Prints a formatted analysis report

**Input Asset**:
- `weather_data_asset`: Imported from `data_fetch.py`, same asset referenced as schedule dependency

**Data Flow**:
```
read_asset() (consumes weather_data_asset from data_fetch)
```

---

## Asset-Based Triggering

This project demonstrates Airflow's **asset-based triggering** pattern:

1. **Producer DAG** (`data_fetch`): Materializes an asset (weather data JSON file)
2. **Consumer DAG** (`data_report`): Depends on the asset and automatically triggers when it's updated

This decouples DAG dependencies from time-based schedules, enabling event-driven workflows.

---

## File Structure

```
Airflow_Project/
├── data_fetch.py       # Producer DAG - fetches and stores weather data
├── data_report.py      # Consumer DAG - reads and analyzes weather data
└── README.md           # This file
```

---

## Storage Location

- **Data Store**: `/opt/airflow/data/`
- **Weather Report File**: `/opt/airflow/data/weather_report.json`

---

## Sample Output

### From `data_fetch` DAG:
```json
{
  "city": "New York",
  "temp": 22,
  "unit": "C",
  "processed_at": "2026-10-05T10:30:45.123456",
  "status": "cleansed"
}
```

### From `data_report` DAG:
```
Analyzing data for New York: 22°C
```

---

## Requirements

- Apache Airflow 2.0+
- Python 3.8+
- Standard library modules: `json`, `os`, `datetime`

---

## Running the DAGs

1. Ensure Airflow is configured and running
2. Place both `.py` files in your Airflow DAGs directory
3. The `data_fetch` DAG will run on its schedule
4. The `data_report` DAG will automatically trigger when the asset is updated
5. Monitor task execution in the Airflow UI

---

## Future Enhancements

- Replace simulated API call with actual weather API integration
- Add error handling and retry logic
- Implement data validation and quality checks
- Extend report generation with multiple output formats
- Add alerting based on temperature thresholds
