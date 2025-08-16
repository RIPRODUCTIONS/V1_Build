# fastapi_endpoint.py
import asyncio
import logging
from typing import Any

import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config_loader import get_airflow_config, load_config
from .core_scraper import run_scraper
from .data_models import ScrapingResult
from .load_data import insert_raw_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Web Scraper API",
    description="API for triggering web scraping workflows and managing scraping operations",
    version="1.0.0"
)

# Request/Response models
class ScrapingRequest(BaseModel):
    """Request model for manual scraping"""
    urls: list[str]
    selectors: dict[str, str]
    next_page_selector: str | None = None
    max_concurrent: int | None = 5
    source_name: str | None = "manual_request"

class AirflowTriggerRequest(BaseModel):
    """Request model for triggering Airflow DAG"""
    dag_id: str | None = None
    conf: dict[str, Any] | None = None
    execution_date: str | None = None

class ScrapingResponse(BaseModel):
    """Response model for scraping operations"""
    success: bool
    message: str
    data: list[dict[str, Any]] | None = None
    total_items: int | None = None
    execution_time: float | None = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str

def trigger_airflow_dag(dag_id: str = None, conf: dict[str, Any] = None) -> dict[str, Any]:
    """
    Trigger an Airflow DAG via HTTP API

    Args:
        dag_id: ID of the DAG to trigger
        conf: Optional configuration for the DAG run

    Returns:
        Dict containing the response from Airflow
    """
    try:
        airflow_config = get_airflow_config()
        dag_id = dag_id or airflow_config['dag_id']

        # Build the Airflow API URL
        base_url = airflow_config['url'].rstrip('/')
        api_version = airflow_config['api_version']
        trigger_url = f"{base_url}/api/{api_version}/dags/{dag_id}/dagRuns"

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
        }

        # Add authentication if provided
        if airflow_config['auth']:
            headers['Authorization'] = f"Basic {airflow_config['auth']}"

        # Prepare payload
        payload = {
            'conf': conf or {},
        }

        if airflow_config.get('execution_date'):
            payload['execution_date'] = airflow_config['execution_date']

        # Make the request
        logger.info(f"Triggering Airflow DAG {dag_id} at {trigger_url}")
        response = requests.post(
            trigger_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully triggered DAG {dag_id}: {result}")
            return {
                'success': True,
                'dag_run_id': result.get('dag_run_id'),
                'message': f"DAG {dag_id} triggered successfully"
            }
        else:
            error_msg = f"Failed to trigger DAG {dag_id}: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error when triggering DAG: {e}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error when triggering DAG: {e}"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }

async def run_scraping_background(request: ScrapingRequest) -> ScrapingResult:
    """
    Run scraping operation in the background

    Args:
        request: Scraping request parameters

    Returns:
        ScrapingResult with the operation results
    """
    start_time = asyncio.get_event_loop().time()

    try:
        # Run the scraper
        raw_results = await run_scraper(
            urls=request.urls,
            selectors=request.selectors,
            next_page_selector=request.next_page_selector,
            max_concurrent=request.max_concurrent
        )

        # Flatten results
        all_data = []
        for page_data in raw_results:
            if isinstance(page_data, list):
                all_data.extend(page_data)
            else:
                all_data.append(page_data)

        # Insert into database if data exists
        if all_data:
            success = insert_raw_data(all_data, request.source_name)
            if not success:
                logger.warning("Failed to insert data into database")

        execution_time = asyncio.get_event_loop().time() - start_time

        return ScrapingResult(
            success=True,
            data=all_data,
            total_items=len(all_data),
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        logger.error(f"Error during background scraping: {e}")

        return ScrapingResult(
            success=False,
            data=[],
            errors=[str(e)],
            execution_time=execution_time
        )

# API Endpoints

@app.get("/", response_model=dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Web Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "trigger_airflow": "/trigger-airflow",
            "scrape_manual": "/scrape-manual",
            "status": "/status"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=asyncio.get_event_loop().time(),
        version="1.0.0"
    )

@app.post("/trigger-airflow", response_model=dict[str, Any])
async def trigger_airflow(request: AirflowTriggerRequest):
    """
    Trigger an Airflow DAG for automated scraping

    Args:
        request: Airflow trigger request parameters

    Returns:
        Response indicating success/failure of DAG trigger
    """
    try:
        result = trigger_airflow_dag(
            dag_id=request.dag_id,
            conf=request.conf
        )

        if result['success']:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": result['message'],
                    "dag_run_id": result.get('dag_run_id')
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )

    except Exception as e:
        logger.error(f"Error triggering Airflow DAG: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger Airflow DAG: {str(e)}"
        )

@app.post("/scrape-manual", response_model=ScrapingResponse)
async def scrape_manual(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Manually trigger a scraping operation

    Args:
        request: Scraping request parameters
        background_tasks: FastAPI background tasks

    Returns:
        Response indicating the scraping operation has been started
    """
    try:
        # Add scraping task to background
        background_tasks.add_task(run_scraping_background, request)

        return ScrapingResponse(
            success=True,
            message=f"Scraping operation started for {len(request.urls)} URLs",
            total_items=0,
            execution_time=0.0
        )

    except Exception as e:
        logger.error(f"Error starting manual scraping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scraping operation: {str(e)}"
        )

@app.get("/status", response_model=dict[str, Any])
async def get_status():
    """Get system status and configuration"""
    try:
        config = load_config()
        airflow_config = get_airflow_config()

        return {
            "status": "operational",
            "config": {
                "max_concurrent": config.get('max_concurrent'),
                "timeout": config.get('timeout'),
                "log_level": config.get('log_level')
            },
            "airflow": {
                "url": airflow_config.get('url'),
                "dag_id": airflow_config.get('dag_id'),
                "api_version": airflow_config.get('api_version')
            }
        }

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system status: {str(e)}"
        )

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    import os

    import uvicorn
    if os.environ.get("RUN_SCRAPER_API") == "1":
        uvicorn.run(
            "fastapi_endpoint:app",
            host="0.0.0.0",
            port=8003,
            reload=False,
            log_level="info"
        )
    else:
        print("scraper/fastapi_endpoint.py entrypoint disabled. Set RUN_SCRAPER_API=1 to run.")
