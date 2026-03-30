"""
Session Cleanup Flow

Scheduled flow for cleaning up old user sessions:
- Clean expired sessions
- Clean orphaned data
- Clean temporary files
- Generate cleanup report
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact


# Database paths
USER_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "users.db")


@task(name="Get Session Statistics", retries=1)
def get_session_statistics(db_path: str) -> Dict[str, Any]:
    """Get current session statistics"""
    logger = get_run_logger()
    logger.info("Getting session statistics")
    
    stats = {
        "total_chat_sessions": 0,
        "total_uploaded_files": 0,
        "total_csv_files": 0,
        "old_sessions": 0,
        "old_files": 0
    }
    
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return stats
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count chat sessions
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history';")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chat_history")
            stats["total_chat_sessions"] = cursor.fetchone()[0]
            
            # Count old sessions (older than 7 days)
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chat_history WHERE timestamp < ?", (cutoff,))
            stats["old_sessions"] = cursor.fetchone()[0]
        
        # Count uploaded documents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_documents';")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM uploaded_documents")
            stats["total_uploaded_files"] = cursor.fetchone()[0]
            
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM uploaded_documents WHERE timestamp < ?", (cutoff,))
            stats["old_files"] += cursor.fetchone()[0]
        
        # Count CSV files
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_csvs';")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM uploaded_csvs")
            stats["total_csv_files"] = cursor.fetchone()[0]
            
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM uploaded_csvs WHERE timestamp < ?", (cutoff,))
            stats["old_files"] += cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"Statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Failed to get session statistics: {str(e)}")
    
    return stats


@task(name="Clean Expired Sessions", retries=1)
def clean_expired_sessions(db_path: str, days_old: int = 7) -> Dict[str, Any]:
    """Clean sessions older than specified days"""
    logger = get_run_logger()
    logger.info(f"Cleaning sessions older than {days_old} days")
    
    result = {
        "chat_sessions_removed": 0,
        "chat_records_removed": 0,
        "documents_removed": 0,
        "csv_records_removed": 0,
        "success": False
    }
    
    if not os.path.exists(db_path):
        return result
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        # Clean chat_history
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history';")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chat_history WHERE timestamp < ?", (cutoff,))
            result["chat_sessions_removed"] = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM chat_history WHERE timestamp < ?", (cutoff,))
            result["chat_records_removed"] = cursor.rowcount
        
        # Clean uploaded_documents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_documents';")
        if cursor.fetchone():
            cursor.execute("DELETE FROM uploaded_documents WHERE timestamp < ?", (cutoff,))
            result["documents_removed"] = cursor.rowcount
        
        # Clean uploaded_csvs
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_csvs';")
        if cursor.fetchone():
            cursor.execute("DELETE FROM uploaded_csvs WHERE timestamp < ?", (cutoff,))
            result["csv_records_removed"] = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        result["success"] = True
        
        total_removed = (result["chat_records_removed"] + result["documents_removed"] + 
                       result["csv_records_removed"])
        logger.info(f"Cleaned {total_removed} records from database")
        
    except Exception as e:
        logger.error(f"Failed to clean sessions: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Clean Orphaned Records", retries=1)
def clean_orphaned_records(db_path: str) -> Dict[str, Any]:
    """Clean records that reference deleted users"""
    logger = get_run_logger()
    logger.info("Cleaning orphaned records")
    
    result = {
        "orphaned_chats": 0,
        "orphaned_documents": 0,
        "orphaned_csvs": 0,
        "success": False
    }
    
    if not os.path.exists(db_path):
        return result
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clean orphaned chat_history
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history';")
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM chat_history 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)
            result["orphaned_chats"] = cursor.rowcount
        
        # Clean orphaned uploaded_documents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_documents';")
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM uploaded_documents 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)
            result["orphaned_documents"] = cursor.rowcount
        
        # Clean orphaned uploaded_csvs
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_csvs';")
        if cursor.fetchone():
            cursor.execute("""
                DELETE FROM uploaded_csvs 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)
            result["orphaned_csvs"] = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        result["success"] = True
        
        total = result["orphaned_chats"] + result["orphaned_documents"] + result["orphaned_csvs"]
        logger.info(f"Cleaned {total} orphaned records")
        
    except Exception as e:
        logger.error(f"Failed to clean orphaned records: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Clean Temporary Files", retries=1)
def clean_temp_files(base_dir: str) -> Dict[str, Any]:
    """Clean temporary files and cache"""
    logger = get_run_logger()
    logger.info("Cleaning temporary files")
    
    result = {
        "files_removed": 0,
        "space_freed_bytes": 0,
        "errors": []
    }
    
    temp_patterns = [".tmp", ".temp", ".cache", "__pycache__"]
    
    try:
        for root, dirs, files in os.walk(base_dir):
            # Skip hidden directories and important paths
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '.venv']]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file matches temp patterns
                if any(pattern in file.lower() for pattern in temp_patterns):
                    try:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        result["files_removed"] += 1
                        result["space_freed_bytes"] += size
                    except Exception as e:
                        result["errors"].append(f"{file_path}: {str(e)}")
        
        logger.info(f"Cleaned {result['files_removed']} temp files, freed {result['space_freed_bytes']} bytes")
        
    except Exception as e:
        logger.error(f"Failed to clean temp files: {str(e)}")
        result["error"] = str(e)
    
    return result


@task(name="Generate Cleanup Report", retries=1)
def generate_cleanup_report(stats: Dict, cleanup_results: List[Dict]) -> str:
    """Generate a cleanup report"""
    logger = get_run_logger()
    
    report = f"""
# Session Cleanup Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics

- Total Chat Sessions: {stats.get('total_chat_sessions', 0)}
- Total Uploaded Files: {stats.get('total_uploaded_files', 0)}
- Total CSV Files: {stats.get('total_csv_files', 0)}

## Cleanup Results

"""
    
    for result in cleanup_results:
        if result.get("success"):
            report += f"- {result.get('chat_records_removed', 0)} chat records removed\n"
            report += f"- {result.get('documents_removed', 0)} documents removed\n"
            report += f"- {result.get('csv_records_removed', 0)} CSV records removed\n"
    
    return report


@flow(name="Cleanup Old Sessions", log_prints=True)
def cleanup_old_sessions(
    days_old: int = 7,
    clean_temp_files: bool = True,
    clean_orphaned: bool = True
) -> Dict[str, Any]:
    """
    Main flow for cleaning up old user sessions.
    
    Args:
        days_old: Delete sessions older than this many days (default: 7)
        clean_temp_files: Whether to clean temporary files (default: True)
        clean_orphaned: Whether to clean orphaned records (default: True)
    
    Returns:
        Dictionary containing cleanup results
    """
    logger = get_run_logger()
    logger.info(f"Starting session cleanup (older than {days_old} days)")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "statistics": {},
        "cleanup_results": {},
        "summary": {
            "records_removed": 0,
            "files_removed": 0,
            "space_freed_bytes": 0
        }
    }
    
    try:
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Step 1: Get initial statistics
        logger.info("Step 1: Getting session statistics")
        stats = get_session_statistics(USER_DB_PATH)
        results["statistics"] = stats
        
        # Step 2: Clean expired sessions
        logger.info("Step 2: Cleaning expired sessions")
        session_result = clean_expired_sessions(USER_DB_PATH, days_old)
        results["cleanup_results"]["expired_sessions"] = session_result
        results["summary"]["records_removed"] += (
            session_result.get("chat_records_removed", 0) +
            session_result.get("documents_removed", 0) +
            session_result.get("csv_records_removed", 0)
        )
        
        # Step 3: Clean orphaned records if requested
        if clean_orphaned:
            logger.info("Step 3: Cleaning orphaned records")
            orphan_result = clean_orphaned_records(USER_DB_PATH)
            results["cleanup_results"]["orphaned"] = orphan_result
            results["summary"]["records_removed"] += (
                orphan_result.get("orphaned_chats", 0) +
                orphan_result.get("orphaned_documents", 0) +
                orphan_result.get("orphaned_csvs", 0)
            )
        
        # Step 4: Clean temporary files if requested
        if clean_temp_files:
            logger.info("Step 4: Cleaning temporary files")
            temp_result = clean_temp_files(base_dir)
            results["cleanup_results"]["temp_files"] = temp_result
            results["summary"]["files_removed"] += temp_result.get("files_removed", 0)
            results["summary"]["space_freed_bytes"] += temp_result.get("space_freed_bytes", 0)
        
        results["success"] = True
        results["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Session cleanup complete: {results['summary']}")
        
        # Create artifact
        records = results["summary"]["records_removed"]
        files = results["summary"]["files_removed"]
        
        create_markdown_artifact(
            f"## Session Cleanup Complete\n\n"
            f"- **Records removed**: {records}\n"
            f"- **Files removed**: {files}\n"
            f"- **Space freed**: {results['summary']['space_freed_bytes']} bytes\n"
            f"- **Time**: {results['completed_at']}"
        )
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        results["error"] = str(e)
    
    return results


# Quick cleanup for scheduled jobs
@flow(name="Quick Session Cleanup")
def quick_cleanup() -> Dict[str, Any]:
    """Quick cleanup for scheduled execution"""
    return cleanup_old_sessions(
        days_old=7,
        clean_temp_files=True,
        clean_orphaned=True
    )

