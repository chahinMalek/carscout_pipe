# CarScout Dashboard

This directory contains the Streamlit-based dashboard for CarScout Pipeline.

## Features
- **Data Exploration**: View records from `Listings`, `Vehicles`, and `Runs` tables.
- **Metrics**: Real-time overview of the pipeline status and data volume.
- **Data Export**: Export any table to **CSV**, **JSON**, or **Parquet**.
- **Search**: Fast filtering of listings by title.

## How to run locally

1. Ensure you have the dependencies installed:
   ```bash
   pip install .
   ```

2. Run the dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```

3. Open your browser at `http://localhost:8501`.

## Docker Integration
The dashboard is integrated as a service in the `docker-compose.yml` configuration.

To run everything including the dashboard:
```bash
docker-compose up -d
```
Access the dashboard at `http://localhost:8501`.
