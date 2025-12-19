from importlib.metadata import version

from celery.result import AsyncResult
from fastapi import FastAPI, status

from worker.main import celery_app

__version__ = version("carscout-pipe")

app = FastAPI(
    title="CarScout Scraping Pipeline",
    description="API for managing vehicle scraping tasks",
    version=__version__,
)


@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
    status_code=status.HTTP_200_OK,
)
def root():
    return {
        "message": "CarScout Scraping Pipeline API",
        "version": __version__,
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Check API health status",
    status_code=status.HTTP_200_OK,
)
def health_check():
    return {
        "status": "healthy",
        "celery_broker": celery_app.conf.broker_url,
    }


@app.post(
    "/api/v1/tasks/listings",
    tags=["Tasks"],
    summary="Start listings scraping task for all brands",
    status_code=status.HTTP_202_ACCEPTED,
)
def start_listings_processing_task():
    from worker.tasks import process_listings

    task = process_listings.delay()
    return {
        "task_id": task.id,
        "task_name": "process_listings",
        "status": "submitted",
    }


@app.post(
    "/api/v1/tasks/vehicles/run/{run_id}",
    tags=["Tasks"],
    summary="Start vehicle details scraping task for a specific run_id",
    status_code=status.HTTP_202_ACCEPTED,
)
def start_vehicles_processing_task_for_run(run_id: str):
    from worker.tasks import process_vehicles

    task = process_vehicles.delay(run_id=run_id)
    return {
        "task_id": task.id,
        "task_name": "process_vehicles",
        "status": "submitted",
    }


@app.post(
    "/api/v1/tasks/pipeline",
    tags=["Tasks"],
    summary="Start full pipeline task",
    status_code=status.HTTP_202_ACCEPTED,
)
def start_pipeline_task():
    from worker.tasks import pipeline

    task = pipeline.delay()
    return {
        "task_id": task.id,
        "task_name": "pipeline",
        "status": "submitted",
    }


@app.get(
    "/api/v1/tasks/{task_id}",
    tags=["Tasks"],
    summary="Get task status",
    status_code=status.HTTP_200_OK,
)
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
        "error": str(result.result) if result.failed() else None,
        "info": result.info,
    }


@app.delete(
    "/api/v1/tasks/{task_id}",
    tags=["Tasks"],
    summary="Cancel/revoke a task",
    status_code=status.HTTP_200_OK,
)
def cancel_task(task_id: str, terminate: bool = False):
    """
    Args:
        task_id: The unique identifier of the task to cancel
        terminate: If True, forcefully terminate the task (SIGKILL).
                   If False (default), send SIGTERM to allow graceful shutdown.

    Returns:
        Confirmation with task ID and cancellation status

    Notes:
        - Pending tasks will be removed from queue
        - Running tasks will be terminated based on the 'terminate' parameter
        - Completed tasks cannot be cancelled
    """
    result = AsyncResult(task_id, app=celery_app)

    # Revoke the task
    result.revoke(terminate=terminate)

    return {
        "task_id": task_id,
        "message": "Task revoked successfully",
        "terminated": terminate,
        "previous_status": result.status,
    }


@app.get(
    "/api/v1/tasks",
    tags=["Tasks"],
    summary="List all tasks",
    status_code=status.HTTP_200_OK,
)
def list_tasks():
    inspect = celery_app.control.inspect()

    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}

    return {
        "active": active,
        "scheduled": scheduled,
        "reserved": reserved,
    }
