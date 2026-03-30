"""
Prefect Flows Package

Contains all Prefect flows for background task processing and scheduled jobs.
"""

# Background Task Processing Flows
from .csv_processing import process_csv_file
from .file_processing import process_uploaded_file
from .model_management import pull_ollama_model, check_model_health

# Scheduled Flows
from .scheduled.database_maintenance import run_database_maintenance
from .scheduled.model_health_check import check_all_models_health
from .scheduled.session_cleanup import cleanup_old_sessions

__all__ = [
    "process_csv_file",
    "process_uploaded_file",
    "pull_ollama_model",
    "check_model_health",
    "run_database_maintenance",
    "check_all_models_health",
    "cleanup_old_sessions",
]

