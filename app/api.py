from celery.result import AsyncResult
from fastapi import FastAPI, status

from worker.main import celery_app

app = FastAPI(
    title="CarScout Scraping Pipeline",
    description="API for managing vehicle scraping tasks",
    version="0.1.0",
)


@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
    status_code=status.HTTP_200_OK,
)
def root():
    """Welcome message with API information."""
    return {
        "message": "CarScout Scraping Pipeline API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Check API health status",
    status_code=status.HTTP_200_OK,
)
def health_check():
    """
    Check if the API and Celery broker are healthy.
    """
    return {
        "status": "healthy",
        "celery_broker": celery_app.conf.broker_url,
    }


@app.post(
    "/api/v1/tasks/listings/{brand_slug}",
    tags=["Tasks"],
    summary="Start brand listings scraping task",
    status_code=status.HTTP_202_ACCEPTED,
)
def start_listings_for_brand_task(brand_slug: str):
    """
    Start a task to scrape vehicle listings for a specific brand.

    Returns:
        TaskSubmitResponse with task ID and status
    """
    from worker.tasks import process_listings_for_brand

    task = process_listings_for_brand.delay(brand_slug=brand_slug)
    return {
        "task_id": task.id,
        "task_name": "process_listings_for_brand",
        "status": "submitted",
    }


@app.post(
    "/api/v1/tasks/listings",
    tags=["Tasks"],
    summary="Start listings scraping task for all brands",
    status_code=status.HTTP_202_ACCEPTED,
)
def start_listings_for_all_brands_task():
    """
    Start a task to scrape vehicle listings for all brands.

    Returns:
        TaskSubmitResponse with task ID and status
    """
    from worker.tasks import spawn_listing_tasks

    task = spawn_listing_tasks.delay()
    return {
        "task_id": task.id,
        "task_name": "spawn_listing_tasks",
        "status": "submitted",
    }


@app.post(
    "/api/v1/tasks/vehicles",
    tags=["Tasks"],
    summary="Start vehicle details scraping task",
    status_code=status.HTTP_202_ACCEPTED,
)
def start_vehicles_task():
    """
    Start a task to scrape detailed vehicle information.

    Returns:
        TaskSubmitResponse with task ID and status
    """
    from worker.tasks import process_vehicles

    task = process_vehicles.delay()
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
    """
    Start the full scraping pipeline (listings + vehicles).

    Returns:
        TaskSubmitResponse with task ID and status
    """
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
    """
    Get the status of a specific task by its ID.

    Args:
        task_id: The unique identifier of the task

    Returns:
        TaskStatusResponse with current status and result (if completed)
    """
    result = AsyncResult(task_id, app=celery_app)

    # Convert result to dict if it's ready and not None
    task_result = None
    if result.ready() and result.result is not None:
        task_result = (
            result.result if isinstance(result.result, dict) else {"value": str(result.result)}
        )

    return {
        "task_id": task_id,
        "status": result.status,
        "result": task_result,
    }


@app.delete(
    "/api/v1/tasks/{task_id}",
    tags=["Tasks"],
    summary="Cancel/revoke a task",
    status_code=status.HTTP_200_OK,
)
def cancel_task(task_id: str, terminate: bool = False):
    """
    Cancel or revoke a running or pending task.

    Args:
        task_id: The unique identifier of the task to cancel
        terminate: If True, forcefully terminate the task (SIGKILL).
                   If False (default), send SIGTERM to allow graceful shutdown.

    Returns:
        Confirmation with task ID and cancellation status

    Note:
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
    """
    List all tasks across different states.

    Returns:
        TaskListResponse containing:
        - active: Tasks currently being executed
        - scheduled: Tasks scheduled for future execution (ETA/countdown)
        - reserved: Tasks pulled by workers but not yet started
    """
    inspect = celery_app.control.inspect()

    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}

    return {
        "active": active,
        "scheduled": scheduled,
        "reserved": reserved,
    }
