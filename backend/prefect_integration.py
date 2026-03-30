"""
Prefect Integration Module

This module provides integration between the FastAPI backend and Prefect flows.
It allows triggering background tasks and scheduled jobs programmatically via API endpoints.

Usage:
    from prefect_integration import trigger_csv_processing, trigger_file_processing, etc.
    
    # Run a background task
    result = trigger_csv_processing(file_path="/path/to/file.csv")
    
    # Or use the API endpoints defined in this module
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prefect import flow, task, get_run_logger
from prefect.deployments import run_deployment
from prefect.orion.schemas.schedules import IntervalSchedule
from prefect.orion.schemas.filters import FlowFilter
from prefect.orion import models, schemas


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Import Prefect flows from prefect_workflows
try:
    from prefect_workflows.flows.csv_processing import process_csv_file
    from prefect_workflows.flows.file_processing import process_uploaded_file
    from prefect_workflows.flows.model_management import pull_ollama_model, check_model_health
    from prefect_workflows.flows.scheduled.database_maintenance import run_database_maintenance
    from prefect_workflows.flows.scheduled.model_health_check import check_all_models_health
    from prefect_workflows.flows.scheduled.session_cleanup import cleanup_old_sessions
    PREFECT_FLOWS_IMPORTED = True
except ImportError as e:
    print(f"Warning: Could not import Prefect flows: {e}")
    PREFECT_FLOWS_IMPORTED = False


# ============================================================================
# Background Task Triggers
# ============================================================================

def trigger_csv_processing(
    file_path: str,
    analysis_type: Optional[str] = None,
    viz_type: str = "histogram",
    wait_for_completion: bool = False
) -> Dict[str, Any]:
    """
    Trigger CSV processing background task.
    
    Args:
        file_path: Path to the CSV file
        analysis_type: Type of analysis (correlation, regression, outliers, distribution)
        viz_type: Type of visualization (histogram, boxplot, heatmap)
        wait_for_completion: Whether to wait for task completion
    
    Returns:
        Dictionary with task info and results
    """
    logger = get_run_logger()
    
    if not PREFECT_FLOWS_IMPORTED:
        return {"error": "Prefect flows not imported", "success": False}
    
    try:
        logger.info(f"Triggering CSV processing for: {file_path}")
        
        # Run the flow
        result = process_csv_file(
            file_path=file_path,
            analysis_type=analysis_type,
            viz_type=viz_type
        )
        
        return {
            "success": True,
            "task_type": "csv_processing",
            "file_path": file_path,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"CSV processing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "task_type": "csv_processing"
        }


def trigger_file_processing(
    file_path: str,
    perform_ocr: bool = False,
    ocr_lang: str = "eng",
    save_text: bool = True
) -> Dict[str, Any]:
    """
    Trigger file processing background task.
    
    Args:
        file_path: Path to the uploaded file
        perform_ocr: Whether to perform OCR on images
        ocr_lang: Language for OCR
        save_text: Whether to save extracted text
    
    Returns:
        Dictionary with task info and results
    """
    logger = get_run_logger()
    
    if not PREFECT_FLOWS_IMPORTED:
        return {"error": "Prefect flows not imported", "success": False}
    
    try:
        logger.info(f"Triggering file processing for: {file_path}")
        
        result = process_uploaded_file(
            file_path=file_path,
            perform_ocr=perform_ocr,
            ocr_lang=ocr_lang,
            save_text=save_text
        )
        
        return {
            "success": True,
            "task_type": "file_processing",
            "file_path": file_path,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File processing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "task_type": "file_processing"
        }


def trigger_model_pull(
    model_name: str,
    skip_if_exists: bool = True
) -> Dict[str, Any]:
    """
    Trigger model pulling background task.
    
    Args:
        model_name: Name of the model to pull
        skip_if_exists: Skip if model already exists
    
    Returns:
        Dictionary with task info and results
    """
    logger = get_run_logger()
    
    if not PREFECT_FLOWS_IMPORTED:
        return {"error": "Prefect flows not imported", "success": False}
    
    try:
        logger.info(f"Triggering model pull: {model_name}")
        
        result = pull_ollama_model(
            model_name=model_name,
            skip_if_exists=skip_if_exists
        )
        
        return {
            "success": True,
            "task_type": "model_pull",
            "model_name": model_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model pull failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "task_type": "model_pull"
        }


# ============================================================================
# Scheduled Job Triggers
# ============================================================================

def trigger_database_maintenance(
    chat_history_days: int = 30,
    session_days: int = 7,
    upload_days: int = 30,
    vacuum: bool = True,
    analyze: bool = True
) -> Dict[str, Any]:
    """
    Trigger database maintenance scheduled job.
    
    Args:
        chat_history_days: Days of chat history to keep
        session_days: Days of session data to keep
        upload_days: Days of uploaded files to keep
        vacuum: Whether to vacuum database
        analyze: Whether to analyze database
    
    Returns:
        Dictionary with job results
    """
    logger = get_run_logger()
    
    if not PREFECT_FLOWS_IMPORTED:
        return {"error": "Prefect flows not imported", "success": False}
    
    try:
        logger.info("Triggering database maintenance")
        
        result = run_database_maintenance(
            chat_history_days=chat_history_days,
            session_days=session_days,
            upload_days=upload_days,
            vacuum=vacuum,
            analyze=analyze
        )
        
        return {
            "success": True,
            "task_type": "database_maintenance",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database maintenance failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "task_type": "database_maintenance"
        }


def trigger_model_health_check(
    models_to_check: Optional[List[str]] = None,
    test_response: bool = True
) -> Dict[str, Any]:
    """
    Trigger model health check scheduled job.
    
    Args:
        models_to_check: Specific models to check (None = all)
        test_response: Whether to test model responses
    
    Returns:
        Dictionary with health check results
    """
    logger = get_run_logger()
    
    if not PREFECT_FLOWS_IMPORTED:
        return {"error": "Prefect flows not imported", "success": False}
    
    try:
        logger.info("Triggering model health check")
        
        result = check_all_models_health(
            models_to_check=models_to_check,
            test_response=test_response
        )
        
        return {
            "success": True,
            "task_type": "model_health_check",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model health check failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "task_type": "model_health_check"
        }


def trigger_session_cleanup(
    days_old: int = 7,
    clean_temp_files: bool = True,
    clean_orphaned: bool = True
) -> Dict[str, Any]:
    """
    Trigger session cleanup scheduled job.
    
    Args:
        days_old: Delete sessions older than this many days
        clean_temp_files: Whether to clean temp files
        clean_orphaned: Whether to clean orphaned records
    
    Returns:
        Dictionary with cleanup results
    """
    logger = get_run_logger()
    
    if not PREFECT_FLOWS_IMPORTED:
        return {"error": "Prefect flows not imported", "success": False}
    
    try:
        logger.info("Triggering session cleanup")
        
        result = cleanup_old_sessions(
            days_old=days_old,
            clean_temp_files=clean_temp_files,
            clean_orphaned=clean_orphaned
        )
        
        return {
            "success": True,
            "task_type": "session_cleanup",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "task_type": "session_cleanup"
        }


# ============================================================================
# FastAPI Integration
# ============================================================================

def create_prefect_routes(app):
    """
    Create FastAPI routes for Prefect integration.
    Call this function with your FastAPI app to add the routes.
    
    Example:
        from fastapi import FastAPI
        from prefect_integration import create_prefect_routes
        
        app = FastAPI()
        create_prefect_routes(app)
    """
    from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
    from pydantic import BaseModel
    from typing import Optional, List
    
    router = APIRouter(prefix="/prefect", tags=["Prefect Tasks"])
    
    # Request models
    class CSVProcessingRequest(BaseModel):
        file_path: str
        analysis_type: Optional[str] = None
        viz_type: str = "histogram"
    
    class FileProcessingRequest(BaseModel):
        file_path: str
        perform_ocr: bool = False
        ocr_lang: str = "eng"
        save_text: bool = True
    
    class ModelPullRequest(BaseModel):
        model_name: str
        skip_if_exists: bool = True
    
    class DBMaintenanceRequest(BaseModel):
        chat_history_days: int = 30
        session_days: int = 7
        upload_days: int = 30
        vacuum: bool = True
        analyze: bool = True
    
    class HealthCheckRequest(BaseModel):
        models_to_check: Optional[List[str]] = None
        test_response: bool = True
    
    class SessionCleanupRequest(BaseModel):
        days_old: int = 7
        clean_temp_files: bool = True
        clean_orphaned: bool = True
    
    # CSV Processing
    @router.post("/csv-process")
    async def process_csv(
        request: CSVProcessingRequest,
        background_tasks: BackgroundTasks
    ):
        """Process CSV file in background"""
        if not PREFECT_FLOWS_IMPORTED:
            raise HTTPException(status_code=500, detail="Prefect not properly configured")
        
        background_tasks.add_task(
            trigger_csv_processing,
            file_path=request.file_path,
            analysis_type=request.analysis_type,
            viz_type=request.viz_type
        )
        
        return {
            "message": "CSV processing started",
            "file_path": request.file_path
        }
    
    # File Processing
    @router.post("/file-process")
    async def process_file(
        request: FileProcessingRequest,
        background_tasks: BackgroundTasks
    ):
        """Process uploaded file in background"""
        if not PREFECT_FLOWS_IMPORTED:
            raise HTTPException(status_code=500, detail="Prefect not properly configured")
        
        background_tasks.add_task(
            trigger_file_processing,
            file_path=request.file_path,
            perform_ocr=request.perform_ocr,
            ocr_lang=request.ocr_lang,
            save_text=request.save_text
        )
        
        return {
            "message": "File processing started",
            "file_path": request.file_path
        }
    
    # Model Pull
    @router.post("/model/pull")
    async def pull_model(
        request: ModelPullRequest,
        background_tasks: BackgroundTasks
    ):
        """Pull Ollama model in background"""
        if not PREFECT_FLOWS_IMPORTED:
            raise HTTPException(status_code=500, detail="Prefect not properly configured")
        
        background_tasks.add_task(
            trigger_model_pull,
            model_name=request.model_name,
            skip_if_exists=request.skip_if_exists
        )
        
        return {
            "message": "Model pull started",
            "model_name": request.model_name
        }
    
    # Database Maintenance
    @router.post("/maintenance/database")
    async def run_db_maintenance(
        request: DBMaintenanceRequest,
        background_tasks: BackgroundTasks
    ):
        """Run database maintenance in background"""
        if not PREFECT_FLOWS_IMPORTED:
            raise HTTPException(status_code=500, detail="Prefect not properly configured")
        
        background_tasks.add_task(
            trigger_database_maintenance,
            chat_history_days=request.chat_history_days,
            session_days=request.session_days,
            upload_days=request.upload_days,
            vacuum=request.vacuum,
            analyze=request.analyze
        )
        
        return {
            "message": "Database maintenance started"
        }
    
    # Model Health Check
    @router.post("/health/check")
    async def check_health(
        request: HealthCheckRequest,
        background_tasks: BackgroundTasks
    ):
        """Run model health check in background"""
        if not PREFECT_FLOWS_IMPORTED:
            raise HTTPException(status_code=500, detail="Prefect not properly configured")
        
        background_tasks.add_task(
            trigger_model_health_check,
            models_to_check=request.models_to_check,
            test_response=request.test_response
        )
        
        return {
            "message": "Model health check started"
        }
    
    # Session Cleanup
    @router.post("/cleanup/sessions")
    async def cleanup_sessions(
        request: SessionCleanupRequest,
        background_tasks: BackgroundTasks
    ):
        """Run session cleanup in background"""
        if not PREFECT_FLOWS_IMPORTED:
            raise HTTPException(status_code=500, detail="Prefect not properly configured")
        
        background_tasks.add_task(
            trigger_session_cleanup,
            days_old=request.days_old,
            clean_temp_files=request.clean_temp_files,
            clean_orphaned=request.clean_orphaned
        )
        
        return {
            "message": "Session cleanup started"
        }
    
    # Status endpoint
    @router.get("/status")
    async def get_status():
        """Get Prefect integration status"""
        return {
            "status": "running" if PREFECT_FLOWS_IMPORTED else "error",
            "flows_imported": PREFECT_FLOWS_IMPORTED,
            "timestamp": datetime.now().isoformat()
        }
    
    return router


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    print("Prefect Integration Module")
    print("=" * 50)
    
    if PREFECT_FLOWS_IMPORTED:
        print("✓ Prefect flows imported successfully")
        
        # Test database maintenance
        print("\nTesting database maintenance...")
        result = trigger_database_maintenance()
        print(f"Result: {result.get('success', False)}")
        
    else:
        print("✗ Failed to import Prefect flows")
        print("Make sure Prefect is installed and flows are properly defined")

