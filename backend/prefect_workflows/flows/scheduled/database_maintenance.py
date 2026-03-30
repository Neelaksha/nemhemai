"""
Database Maintenance Flow

Scheduled flow for database cleanup and maintenance:
- Clean old records
- Optimize database
- Vacuum SQLite database
- Remove orphaned records
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact


# Database paths - adjust these to match your application
USER_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "users.db")
ANALYSIS_DB_PATH = "databases/analysis.db"


@task(name="Get Database Info", retries=1)
def get_db_info(db_path: str) -> Dict[str, Any]:
    """Get information about a SQLite database"""
    logger = get_run_logger()
    logger.info(f"Getting info for database: {db_path}")
    
    info = {
        "path": db_path,
        "exists": False,
        "size_bytes": 0,
        "tables": []
    }
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return info
    
    info["exists"] = True
    info["size_bytes"] = os.path.getsize(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        info["tables"] = [t[0] for t in tables]
        
        # Get row counts
        for table in info["tables"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            info[f"{table}_count"] = count
        
        conn.close()
        
        logger.info(f"Database info: {len(info['tables'])} tables, {info['size_bytes']} bytes")
        
    except Exception as e:
        logger.error(f"Failed to get database info: {str(e)}")
        info["error"] = str(e)
    
    return info


@task(name="Clean Old Chat History", retries=1)
def clean_old_chat_history(db_path: str, days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean old chat history records"""
    logger = get_run_logger()
    logger.info(f"Cleaning chat history older than {days_to_keep} days")
    
    result = {
        "records_deleted": 0,
        "success": False
    }
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return result
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history';")
        if not cursor.fetchone():
            logger.info("chat_history table does not exist, skipping")
            conn.close()
            result["success"] = True
            return result
        
        # Get count before
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        count_before = cursor.fetchone()[0]
        
        # Delete old records
        cursor.execute(
            "DELETE FROM chat_history WHERE timestamp < ?",
            (cutoff_date.isoformat(),)
        )
        
        result["records_deleted"] = count_before - cursor.rowcount
        conn.commit()
        
        # Get count after
        cursor.execute("SELECT COUNT(*) FROM chat_history")
        count_after = cursor.fetchone()[0]
        
        conn.close()
        
        result["success"] = True
        result["count_before"] = count_before
        result["count_after"] = count_after
        
        logger.info(f"Deleted {result['records_deleted']} old chat history records")
        
    except Exception as e:
        logger.error(f"Failed to clean chat history: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Clean Old Sessions", retries=1)
def clean_old_sessions(db_path: str, days_to_keep: int = 7) -> Dict[str, Any]:
    """Clean old session data"""
    logger = get_run_logger()
    logger.info(f"Cleaning sessions older than {days_to_keep} days")
    
    result = {
        "success": False,
        "tables_cleaned": []
    }
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return result
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Tables that might have session data
        session_tables = [
            "chat_history", 
            "uploaded_documents", 
            "uploaded_csvs"
        ]
        
        for table in session_tables:
            try:
                # Check if table exists and has session_id and timestamp
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
                if not cursor.fetchone():
                    continue
                
                # Check if table has timestamp column
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'timestamp' in columns:
                    # Get count before
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count_before = cursor.fetchone()[0]
                    
                    # Delete old records
                    cursor.execute(
                        f"DELETE FROM {table} WHERE timestamp < ?",
                        (cutoff_date.isoformat(),)
                    )
                    
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        result["tables_cleaned"].append({
                            "table": table,
                            "deleted": cursor.rowcount
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to clean table {table}: {str(e)}")
                continue
        
        conn.close()
        result["success"] = True
        
    except Exception as e:
        logger.error(f"Failed to clean sessions: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Clean Uploaded Files", retries=1)
def clean_uploaded_files(base_dir: str, days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean old uploaded files from filesystem"""
    logger = get_run_logger()
    logger.info(f"Cleaning uploaded files older than {days_to_keep} days")
    
    result = {
        "files_deleted": 0,
        "space_freed_bytes": 0,
        "success": False
    }
    
    if not os.path.exists(base_dir):
        logger.warning(f"Directory not found: {base_dir}")
        return result
    
    try:
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        # Directories to clean
        dirs_to_clean = ["uploads", "csv_uploads"]
        
        for dir_name in dirs_to_clean:
            dir_path = os.path.join(base_dir, dir_name)
            
            if not os.path.exists(dir_path):
                continue
            
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_mtime < cutoff_time:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            result["files_deleted"] += 1
                            result["space_freed_bytes"] += file_size
                            logger.info(f"Deleted: {file_path}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to process {file_path}: {str(e)}")
        
        result["success"] = True
        logger.info(f"Deleted {result['files_deleted']} files, freed {result['space_freed_bytes']} bytes")
        
    except Exception as e:
        logger.error(f"Failed to clean uploaded files: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Vacuum Database", retries=1)
def vacuum_database(db_path: str) -> Dict[str, Any]:
    """Run VACUUM to optimize SQLite database"""
    logger = get_run_logger()
    logger.info(f"Vacuuming database: {db_path}")
    
    result = {
        "success": False,
        "size_before": 0,
        "size_after": 0
    }
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return result
    
    try:
        result["size_before"] = os.path.getsize(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Run VACUUM
        cursor.execute("VACUUM;")
        conn.commit()
        conn.close()
        
        result["size_after"] = os.path.getsize(db_path)
        result["space_saved"] = result["size_before"] - result["size_after"]
        result["success"] = True
        
        logger.info(f"Vacuum complete: {result['size_before']} -> {result['size_after']} bytes")
        
    except Exception as e:
        logger.error(f"Failed to vacuum database: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Analyze Database", retries=1)
def analyze_database(db_path: str) -> Dict[str, Any]:
    """Run ANALYZE to update statistics"""
    logger = get_run_logger()
    logger.info(f"Analyzing database: {db_path}")
    
    result = {
        "success": False
    }
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return result
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Run ANALYZE
        cursor.execute("ANALYZE;")
        conn.commit()
        conn.close()
        
        result["success"] = True
        logger.info("Database analysis complete")
        
    except Exception as e:
        logger.error(f"Failed to analyze database: {str(e)}")
        result["error"] = str(e)
    
    return result


@flow(name="Run Database Maintenance", log_prints=True)
def run_database_maintenance(
    chat_history_days: int = 30,
    session_days: int = 7,
    upload_days: int = 30,
    vacuum: bool = True,
    analyze: bool = True
) -> Dict[str, Any]:
    """
    Main flow for database maintenance.
    
    Args:
        chat_history_days: Days of chat history to keep (default: 30)
        session_days: Days of session data to keep (default: 7)
        upload_days: Days of uploaded files to keep (default: 30)
        vacuum: Whether to vacuum the database (default: True)
        analyze: Whether to analyze the database (default: True)
    
    Returns:
        Dictionary containing maintenance results
    """
    logger = get_run_logger()
    logger.info("Starting database maintenance")
    
    results = {
        "started_at": datetime.now().isoformat(),
        "success": False,
        "operations": {}
    }
    
    try:
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # 1. Get initial database info
        logger.info("Step 1: Getting initial database info")
        results["operations"]["initial_info"] = get_db_info(USER_DB_PATH)
        
        # 2. Clean old chat history
        logger.info("Step 2: Cleaning old chat history")
        results["operations"]["chat_cleanup"] = clean_old_chat_history(
            USER_DB_PATH, 
            chat_history_days
        )
        
        # 3. Clean old sessions
        logger.info("Step 3: Cleaning old sessions")
        results["operations"]["session_cleanup"] = clean_old_sessions(
            USER_DB_PATH,
            session_days
        )
        
        # 4. Clean old uploaded files
        logger.info("Step 4: Cleaning old uploaded files")
        results["operations"]["file_cleanup"] = clean_uploaded_files(
            base_dir,
            upload_days
        )
        
        # 5. Vacuum database if requested
        if vacuum:
            logger.info("Step 5: Vacuuming database")
            results["operations"]["vacuum"] = vacuum_database(USER_DB_PATH)
        
        # 6. Analyze database if requested
        if analyze:
            logger.info("Step 6: Analyzing database")
            results["operations"]["analyze"] = analyze_database(USER_DB_PATH)
        
        # 7. Get final database info
        logger.info("Step 7: Getting final database info")
        results["operations"]["final_info"] = get_db_info(USER_DB_PATH)
        
        results["success"] = True
        results["completed_at"] = datetime.now().isoformat()
        
        logger.info("Database maintenance completed successfully")
        
        # Create artifact
        chat_deleted = results["operations"]["chat_cleanup"].get("records_deleted", 0)
        files_deleted = results["operations"]["file_cleanup"].get("files_deleted", 0)
        
        create_markdown_artifact(
            f"## Database Maintenance Complete\n\n"
            f"- **Chat records deleted**: {chat_deleted}\n"
            f"- **Files deleted**: {files_deleted}\n"
            f"- **Success**: {results['success']}"
        )
        
    except Exception as e:
        logger.error(f"Database maintenance failed: {str(e)}")
        results["error"] = str(e)
    
    return results

