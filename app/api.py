from celery.result import AsyncResult
from fastapi import FastAPI

from worker.main import celery_app

app = FastAPI(
    title="CarScout Scraping Pipeline",
    description="API for managing vehicle scraping tasks",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "celery_broker": celery_app.conf.broker_url,
    }


@app.post("/tasks/listings")
def start_listings_task():
    from worker.tasks import process_listings

    task = process_listings.delay()
    return {
        "task_id": task.id,
        "task_name": "process_listings",
        "status": "submitted",
    }


@app.post("/tasks/vehicles")
def start_vehicles_task():
    from worker.tasks import process_vehicles

    task = process_vehicles.delay()
    return {
        "task_id": task.id,
        "task_name": "process_vehicles",
        "status": "submitted",
    }


@app.post("/tasks/pipeline")
def start_pipeline_task():
    from worker.tasks import pipeline

    task = pipeline.delay()
    return {
        "task_id": task.id,
        "task_name": "pipeline",
        "status": "submitted",
    }


@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
