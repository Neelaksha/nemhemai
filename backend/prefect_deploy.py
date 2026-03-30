#!/usr/bin/env python3
"""
Prefect Deployment Script

This script helps deploy and run Prefect flows for the Nemhem application.
It provides commands for:
- Running flows directly
- Setting up scheduled deployments
- Testing flows

Usage:
    python prefect_deploy.py run <flow_name>
    python prefect_deploy.py deploy
    python prefect_deploy.py test
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import flows from prefect_workflows (not prefect to avoid conflict with actual Prefect library)
try:
    from prefect_workflows.flows.csv_processing import process_csv_file
    from prefect_workflows.flows.file_processing import process_uploaded_file
    from prefect_workflows.flows.model_management import pull_ollama_model, check_model_health
    from prefect_workflows.flows.scheduled.database_maintenance import run_database_maintenance
    from prefect_workflows.flows.scheduled.model_health_check import check_all_models_health
    from prefect_workflows.flows.scheduled.session_cleanup import cleanup_old_sessions
    WORKFLOWS_IMPORTED = True
except ImportError as e:
    print(f"Warning: Could not import workflows: {e}")
    WORKFLOWS_IMPORTED = False


def run_flow(flow_name: str, **kwargs):
    """Run a specific Prefect flow"""
    print(f"Running flow: {flow_name}")
    
    if not WORKFLOWS_IMPORTED:
        print("Error: Workflows not imported. Make sure prefect_workflows is properly set up.")
        return False
    
    flows = {
        "csv-process": process_csv_file,
        "file-process": process_uploaded_file,
        "model-pull": pull_ollama_model,
        "model-health": check_model_health,
        "db-maintenance": run_database_maintenance,
        "health-check": check_all_models_health,
        "session-cleanup": cleanup_old_sessions,
    }
    
    if flow_name not in flows:
        print(f"Error: Unknown flow '{flow_name}'")
        print(f"Available flows: {', '.join(flows.keys())}")
        return False
    
    flow = flows[flow_name]
    result = flow(**kwargs)
    
    print(f"Flow completed: {result}")
    return True


def deploy_schedules():
    """Deploy scheduled flows"""
    print("Deploying scheduled flows...")
    
    schedules = """
# Add these to your crontab for scheduled execution:

# Database maintenance - daily at 2 AM
0 2 * * * cd /path/to/backend && python prefect_deploy.py run db-maintenance

# Model health check - every hour
0 * * * * cd /path/to/backend && python prefect_deploy.py run health-check

# Session cleanup - daily at 3 AM
0 3 * * * cd /path/to/backend && python prefect_deploy.py run session-cleanup
"""
    print(schedules)
    return True


def test_flows():
    """Test all flows"""
    print("Testing Prefect flows...")
    
    tests = [
        ("Model Health Check", lambda: run_flow("health-check")),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Testing: {name} ---")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Test failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
    
    return all(r for _, r in results)


def start_prefect_server():
    """Start Prefect server"""
    print("Starting Prefect server...")
    subprocess.run(["prefect", "server", "start"])


def main():
    parser = argparse.ArgumentParser(description="Prefect Deployment Script")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run flow command
    run_parser = subparsers.add_parser("run", help="Run a Prefect flow")
    run_parser.add_argument("flow_name", help="Name of the flow to run")
    run_parser.add_argument("--csv-file", help="CSV file path for csv-process flow")
    run_parser.add_argument("--file", help="File path for file-process flow")
    run_parser.add_argument("--model", help="Model name for model-pull flow")
    run_parser.add_argument("--analysis", help="Analysis type for csv-process")
    
    # Deploy command
    subparsers.add_parser("deploy", help="Deploy scheduled flows")
    
    # Test command
    subparsers.add_parser("test", help="Test all flows")
    
    # Server command
    subparsers.add_parser("server", help="Start Prefect server")
    
    args = parser.parse_args()
    
    if args.command == "run":
        kwargs = {}
        if args.flow_name == "csv-process" and args.csv_file:
            kwargs["file_path"] = args.csv_file
            if args.analysis:
                kwargs["analysis_type"] = args.analysis
        elif args.flow_name == "file-process" and args.file:
            kwargs["file_path"] = args.file
        elif args.flow_name == "model-pull" and args.model:
            kwargs["model_name"] = args.model
        
        success = run_flow(args.flow_name, **kwargs)
        sys.exit(0 if success else 1)
        
    elif args.command == "deploy":
        success = deploy_schedules()
        sys.exit(0 if success else 1)
        
    elif args.command == "test":
        success = test_flows()
        sys.exit(0 if success else 1)
        
    elif args.command == "server":
        start_prefect_server()
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

