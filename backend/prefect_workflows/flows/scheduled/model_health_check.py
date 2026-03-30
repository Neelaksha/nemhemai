"""
Model Health Check Flow

Scheduled flow for checking the health of Ollama models:
- Verify Ollama service is running
- Test each model
- Report model status
- Send notifications (optional)
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@task(name="Check Ollama Service Status", retries=2, retry_delay_seconds=5)
def check_ollama_service_status() -> Dict[str, Any]:
    """Check if Ollama service is running"""
    logger = get_run_logger()
    logger.info("Checking Ollama service status...")
    
    result = {
        "running": False,
        "port_open": False,
        "api_responsive": False,
        "version": None
    }
    
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        port_result = s.connect_ex(('localhost', 11434))
        s.close()
        
        result["port_open"] = port_result == 0
        
        if result["port_open"]:
            # Try to get version
            try:
                import requests
                response = requests.get("http://localhost:11434/api/version", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    result["version"] = data.get("version")
                    result["api_responsive"] = True
                    result["running"] = True
            except Exception as e:
                logger.warning(f"Failed to get Ollama version: {str(e)}")
        
        logger.info(f"Ollama service status: running={result['running']}")
        
    except Exception as e:
        logger.error(f"Failed to check Ollama service: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="List All Models", retries=1)
def list_all_models() -> List[Dict[str, Any]]:
    """List all available Ollama models"""
    logger = get_run_logger()
    logger.info("Listing all Ollama models...")
    
    models = []
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            
            # Skip header
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        models.append({
                            "name": parts[0],
                            "id": parts[1],
                            "size": parts[2],
                            "modified": " ".join(parts[3:]) if len(parts) > 3 else ""
                        })
        
        logger.info(f"Found {len(models)} models")
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
    
    return models


@task(name="Test Model Response", retries=1)
def test_model_response(model_name: str, timeout: int = 30) -> Dict[str, Any]:
    """Test if a model responds correctly"""
    logger = get_run_logger()
    
    result = {
        "model": model_name,
        "success": False,
        "latency_ms": None,
        "response_length": None,
        "error": None
    }
    
    import time
    start_time = time.time()
    
    try:
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "Say 'OK' if you can hear me.",
                "stream": False,
                "options": {
                    "num_predict": 20,
                    "temperature": 0
                }
            },
            timeout=timeout
        )
        
        result["latency_ms"] = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            resp_text = data.get("response", "")
            result["success"] = True
            result["response_length"] = len(resp_text)
            result["response_preview"] = resp_text[:100]
        else:
            result["error"] = f"HTTP {response.status_code}"
            
    except Exception as e:
        result["error"] = str(e)
        result["latency_ms"] = int((time.time() - start_time) * 1000)
    
    return result


@task(name="Get Model Details", retries=1)
def get_model_details(model_name: str) -> Dict[str, Any]:
    """Get detailed information about a model"""
    logger = get_run_logger()
    
    details = {
        "name": model_name,
        "exists": False,
        "info": None
    }
    
    try:
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=10
        )
        
        if response.status_code == 200:
            details["exists"] = True
            details["info"] = response.json()
        else:
            details["error"] = f"HTTP {response.status_code}"
            
    except Exception as e:
        details["error"] = str(e)
    
    return details


@flow(name="Check All Models Health", log_prints=True)
def check_all_models_health(
    models_to_check: Optional[List[str]] = None,
    test_response: bool = True,
    alert_on_failure: bool = False
) -> Dict[str, Any]:
    """
    Main flow for checking health of all Ollama models.
    
    Args:
        models_to_check: Specific models to check (default: all available)
        test_response: Whether to test model responses (default: True)
        alert_on_failure: Whether to send alerts on failure (default: False)
    
    Returns:
        Dictionary containing health check results
    """
    logger = get_run_logger()
    logger.info("Starting model health check")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "service_status": None,
        "models": [],
        "summary": {
            "total": 0,
            "healthy": 0,
            "unhealthy": 0,
            "degraded": 0
        }
    }
    
    try:
        # Step 1: Check Ollama service
        logger.info("Step 1: Checking Ollama service")
        service_status = check_ollama_service_status()
        results["service_status"] = service_status
        
        if not service_status["running"]:
            logger.error("Ollama service is not running!")
            results["error"] = "Ollama service is not running"
            
            # Create artifact for failure
            create_markdown_artifact(
                f"## Model Health Check - FAILED\n\n"
                f"- **Ollama Service**: Not Running\n"
                f"- **Time**: {results['timestamp']}\n"
                f"- **Action Required**: Start Ollama service"
            )
            return results
        
        # Step 2: Get list of models
        logger.info("Step 2: Getting model list")
        available_models = list_all_models()
        
        if not available_models:
            logger.warning("No models found")
            results["warning"] = "No models found"
        
        # Filter models to check
        if models_to_check:
            models_to_check = [m for m in models_to_check if any(m in am["name"] for am in available_models)]
        else:
            models_to_check = [m["name"] for m in available_models]
        
        results["summary"]["total"] = len(models_to_check)
        
        # Step 3: Check each model
        logger.info(f"Step 3: Checking {len(models_to_check)} models")
        
        for model_name in models_to_check:
            model_result = {
                "name": model_name,
                "status": HealthStatus.UNKNOWN.value,
                "test_result": None,
                "details": None
            }
            
            # Get model details
            details = get_model_details(model_name)
            model_result["details"] = details
            
            if not details.get("exists"):
                model_result["status"] = HealthStatus.UNHEALTHY.value
                results["summary"]["unhealthy"] += 1
            else:
                # Test response if requested
                if test_response:
                    test_result = test_model_response(model_name)
                    model_result["test_result"] = test_result
                    
                    if test_result["success"]:
                        model_result["status"] = HealthStatus.HEALTHY.value
                        results["summary"]["healthy"] += 1
                    else:
                        model_result["status"] = HealthStatus.UNHEALTHY.value
                        results["summary"]["unhealthy"] += 1
                else:
                    model_result["status"] = HealthStatus.HEALTHY.value
                    results["summary"]["healthy"] += 1
            
            results["models"].append(model_result)
            logger.info(f"Model {model_name}: {model_result['status']}")
        
        results["success"] = True
        
        # Create artifact
        healthy_count = results["summary"]["healthy"]
        total_count = results["summary"]["total"]
        
        create_markdown_artifact(
            f"## Model Health Check Complete\n\n"
            f"- **Total Models**: {total_count}\n"
            f"- **Healthy**: {healthy_count}\n"
            f"- **Unhealthy**: {results['summary']['unhealthy']}\n"
            f"- **Time**: {results['timestamp']}"
        )
        
        # Log summary
        logger.info(f"Health check complete: {healthy_count}/{total_count} models healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        results["error"] = str(e)
    
    return results


# Standalone function for quick health check
@flow(name="Quick Model Health Check")
def quick_health_check() -> Dict[str, Any]:
    """Quick health check without detailed testing"""
    logger = get_run_logger()
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "healthy": False
    }
    
    try:
        # Check service
        service = check_ollama_service_status()
        result["service_running"] = service["running"]
        result["service_version"] = service.get("version")
        
        if not service["running"]:
            result["message"] = "Ollama service is not running"
            return result
        
        # Get models
        models = list_all_models()
        result["model_count"] = len(models)
        result["models"] = [m["name"] for m in models]
        
        # Test first model if available
        if models:
            test = test_model_response(models[0]["name"], timeout=15)
            result["healthy"] = test["success"]
            result["test_model"] = models[0]["name"]
            result["test_latency_ms"] = test.get("latency_ms")
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

