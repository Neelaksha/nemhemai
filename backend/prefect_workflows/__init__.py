"""
Prefect Integration for Nemhem Backend

This package provides Prefect-based workflows for:
- Background Task Processing (CSV, file, model management)
- Scheduled Jobs (database maintenance, model health checks, session cleanup)
"""

from prefect import flow, task
from prefect.logging import get_run_logger

__version__ = "1.0.0"

# Import flows from local modules (not from actual prefect library)
from prefect_workflows.flows.csv_processing import process_csv_file
from prefect_workflows.flows.file_processing import process_uploaded_file
from prefect_workflows.flows.model_management import pull_ollama_model, check_model_health
from prefect_workflows.flows.scheduled.database_maintenance import run_database_maintenance
from prefect_workflows.flows.scheduled.model_health_check import check_all_models_health
from prefect_workflows.flows.scheduled.session_cleanup import cleanup_old_sessions

__all__ = [
    "process_csv_file",
    "process_uploaded_file", 
    "pull_ollama_model",
    "check_model_health",
    "run_database_maintenance",
    "check_all_models_health",
    "cleanup_old_sessions",
]

