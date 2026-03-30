"""
Model Management Flow

Background task flow for managing Ollama models:
- Pulling models from registry
- Model health checks
- Model listing and status
"""

import os
import subprocess
import json
from typing import Optional, Dict, Any, List
from enum import Enum

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact


class ModelStatus(Enum):
    AVAILABLE = "available"
    NOT_FOUND = "not_found"
    ERROR = "error"
    PULLING = "pulling"


@task(name="Check Ollama Service", retries=3, retry_delay_seconds=5)
def check_ollama_service() -> bool:
    """Check if Ollama service is running"""
    logger = get_run_logger()
    logger.info("Checking Ollama service status...")
    
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex(('localhost', 11434))
        s.close()
        
        if result == 0:
            logger.info("Ollama service is running")
            return True
        else:
            logger.warning("Ollama service is not running")
            return False
    except Exception as e:
        logger.error(f"Failed to check Ollama service: {str(e)}")
        return False


@task(name="List Local Models", retries=1)
def list_local_models() -> List[Dict[str, str]]:
    """List all locally available models"""
    logger = get_run_logger()
    logger.info("Listing local Ollama models...")
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to list models: {result.stderr}")
            return []
        
        # Parse the output
        lines = result.stdout.strip().split('\n')
        models = []
        
        # Skip header line
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
        
        logger.info(f"Found {len(models)} local models")
        return models
        
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        return []


@task(name="Check Model Exists", retries=1)
def check_model_exists(model_name: str) -> bool:
    """Check if a specific model exists locally"""
    logger = get_run_logger()
    logger.info(f"Checking if model exists: {model_name}")
    
    models = list_local_models()
    return any(m["name"] == model_name for m in models)


@task(name="Pull Ollama Model", retries=2, retry_delay_seconds=30)
def pull_model_task(model_name: str, stream: bool = True) -> Dict[str, Any]:
    """Pull a model from Ollama registry"""
    logger = get_run_logger()
    logger.info(f"Pulling model: {model_name}")
    
    result = {
        "model_name": model_name,
        "success": False,
        "status": "starting",
        "logs": []
    }
    
    try:
        cmd = ["ollama", "pull", model_name]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                result["logs"].append(line.strip())
                logger.info(f"Pull: {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            result["success"] = True
            result["status"] = "success"
            logger.info(f"Successfully pulled model: {model_name}")
        else:
            result["status"] = "failed"
            logger.error(f"Failed to pull model: {model_name}")
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Error pulling model: {str(e)}")
    
    return result


@task(name="Remove Model", retries=1)
def remove_model_task(model_name: str) -> Dict[str, Any]:
    """Remove a model from local storage"""
    logger = get_run_logger()
    logger.info(f"Removing model: {model_name}")
    
    result = {
        "model_name": model_name,
        "success": False
    }
    
    try:
        cmd = ["ollama", "rm", model_name]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if process.returncode == 0:
            result["success"] = True
            logger.info(f"Successfully removed model: {model_name}")
        else:
            result["error"] = process.stderr
            logger.error(f"Failed to remove model: {process.stderr}")
            
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error removing model: {str(e)}")
    
    return result


@task(name="Test Model", retries=1)
def test_model_task(model_name: str, prompt: str = "Hello") -> Dict[str, Any]:
    """Test if a model is working by generating a simple response"""
    logger = get_run_logger()
    logger.info(f"Testing model: {model_name}")
    
    result = {
        "model_name": model_name,
        "success": False,
        "response": None,
        "latency": None
    }
    
    import time
    start_time = time.time()
    
    try:
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 50
                }
            },
            timeout=60
        )
        
        result["latency"] = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            result["success"] = True
            result["response"] = data.get("response", "").strip()[:200]
            logger.info(f"Model test successful: {model_name}")
        else:
            result["error"] = f"HTTP {response.status_code}"
            logger.error(f"Model test failed: {response.status_code}")
            
    except Exception as e:
        result["error"] = str(e)
        result["latency"] = time.time() - start_time
        logger.error(f"Model test error: {str(e)}")
    
    return result


@task(name="Check Model Health", retries=1)
def check_model_health_task(model_name: str) -> Dict[str, Any]:
    """Check the health status of a model"""
    logger = get_run_logger()
    logger.info(f"Checking health of model: {model_name}")
    
    result = {
        "model_name": model_name,
        "exists": False,
        "status": ModelStatus.NOT_FOUND.value,
        "test_result": None
    }
    
    # Check if model exists
    models = list_local_models()
    model_exists = any(m["name"] == model_name for m in models)
    
    if not model_exists:
        result["status"] = ModelStatus.NOT_FOUND.value
        return result
    
    result["exists"] = True
    result["status"] = ModelStatus.AVAILABLE.value
    
    # Try to test the model
    test_result = test_model_task(model_name)
    result["test_result"] = test_result
    
    if test_result.get("success"):
        result["status"] = ModelStatus.AVAILABLE.value
    else:
        result["status"] = ModelStatus.ERROR.value
    
    return result


@flow(name="Pull Ollama Model", log_prints=True)
def pull_ollama_model(
    model_name: str,
    skip_if_exists: bool = True
) -> Dict[str, Any]:
    """
    Flow to pull an Ollama model.
    
    Args:
        model_name: Name of the model to pull
        skip_if_exists: Skip pulling if model already exists
    
    Returns:
        Dictionary containing pull result
    """
    logger = get_run_logger()
    logger.info(f"Starting model pull for: {model_name}")
    
    results = {
        "model_name": model_name,
        "success": False
    }
    
    try:
        # Step 1: Check if Ollama service is running
        service_running = check_ollama_service()
        if not service_running:
            results["error"] = "Ollama service is not running"
            logger.error(results["error"])
            return results
        
        # Step 2: Check if model already exists
        if skip_if_exists:
            exists = check_model_exists(model_name)
            if exists:
                results["success"] = True
                results["message"] = f"Model {model_name} already exists"
                logger.info(results["message"])
                return results
        
        # Step 3: Pull the model
        pull_result = pull_model_task(model_name)
        results.update(pull_result)
        
        # Create artifact
        if pull_result["success"]:
            create_markdown_artifact(
                f"## Model Pull Complete\n\n"
                f"- **Model**: {model_name}\n"
                f"- **Status**: Success"
            )
        
    except Exception as e:
        logger.error(f"Model pull failed: {str(e)}")
        results["error"] = str(e)
    
    return results


@flow(name="Check Model Health", log_prints=True)
def check_model_health(model_name: str) -> Dict[str, Any]:
    """
    Flow to check the health of a specific model.
    
    Args:
        model_name: Name of the model to check
    
    Returns:
        Dictionary containing health status
    """
    logger = get_run_logger()
    logger.info(f"Starting health check for: {model_name}")
    
    try:
        # Check service first
        service_running = check_ollama_service()
        if not service_running:
            return {
                "model_name": model_name,
                "status": "error",
                "error": "Ollama service not running"
            }
        
        # Check model health
        result = check_model_health_task(model_name)
        return result
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "model_name": model_name,
            "status": "error",
            "error": str(e)
        }


@flow(name="Manage Multiple Models")
def manage_models(
    models_to_pull: Optional[List[str]] = None,
    models_to_remove: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Flow to manage multiple models (pull and/or remove).
    
    Args:
        models_to_pull: List of model names to pull
        models_to_remove: List of model names to remove
    
    Returns:
        Dictionary containing results for all operations
    """
    logger = get_run_logger()
    results = {
        "pulled": [],
        "removed": [],
        "errors": []
    }
    
    # Pull models
    if models_to_pull:
        for model in models_to_pull:
            try:
                result = pull_ollama_model(model)
                if result.get("success"):
                    results["pulled"].append(model)
                else:
                    results["errors"].append(f"Failed to pull {model}: {result.get('error')}")
            except Exception as e:
                results["errors"].append(f"Error pulling {model}: {str(e)}")
    
    # Remove models
    if models_to_remove:
        for model in models_to_remove:
            try:
                result = remove_model_task(model)
                if result.get("success"):
                    results["removed"].append(model)
                else:
                    results["errors"].append(f"Failed to remove {model}: {result.get('error')}")
            except Exception as e:
                results["errors"].append(f"Error removing {model}: {str(e)}")
    
    return results

