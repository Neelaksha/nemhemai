"""Database connector utilities for various database types"""

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from typing import Dict, List, Optional, Tuple
import urllib.parse


class DatabaseConnector:
    """Unified database connector for multiple database types"""
    
    SUPPORTED_DB_TYPES = ['mysql', 'postgresql', 'sqlite', 'sqlserver', 'oracle']
    
    @staticmethod
    def build_connection_string(
        db_type: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        custom_string: Optional[str] = None
    ) -> str:
        """Build SQLAlchemy connection string for different database types"""
        
        if custom_string:
            return custom_string
        
        db_type = db_type.lower()
        
        if db_type == 'sqlite':
            # SQLite uses file path
            return f"sqlite:///{database}"
        
        elif db_type == 'mysql':
            # MySQL connection string
            encoded_password = urllib.parse.quote_plus(password) if password else ""
            port = port or 3306
            return f"mysql+pymysql://{username}:{encoded_password}@{host}:{port}/{database}"
        
        elif db_type == 'postgresql':
            # PostgreSQL connection string
            encoded_password = urllib.parse.quote_plus(password) if password else ""
            port = port or 5432
            return f"postgresql+psycopg2://{username}:{encoded_password}@{host}:{port}/{database}"
        
        elif db_type == 'sqlserver':
            # SQL Server connection string
            encoded_password = urllib.parse.quote_plus(password) if password else ""
            port = port or 1433
            driver = "ODBC+Driver+17+for+SQL+Server"
            return f"mssql+pyodbc://{username}:{encoded_password}@{host}:{port}/{database}?driver={driver}"
        
        elif db_type == 'oracle':
            # Oracle connection string
            encoded_password = urllib.parse.quote_plus(password) if password else ""
            port = port or 1521
            return f"oracle+cx_oracle://{username}:{encoded_password}@{host}:{port}/{database}"
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def test_connection(connection_string: str) -> Tuple[bool, str]:
        """Test database connection"""
        try:
            # Different databases use different timeout parameters
            connect_args = {}
            if 'sqlite' in connection_string:
                connect_args = {"timeout": 5}
            elif 'mysql' in connection_string:
                connect_args = {"connect_timeout": 5}
            elif 'postgresql' in connection_string:
                connect_args = {"connect_timeout": 5}
            
            engine = create_engine(connection_string, connect_args=connect_args)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connection successful!"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    @staticmethod
    def get_tables(connection_string: str) -> List[str]:
        """Get list of tables from database"""
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            return inspector.get_table_names()
        except Exception as e:
            raise Exception(f"Failed to get tables: {str(e)}")
    
    @staticmethod
    def get_table_info(connection_string: str, table_name: str) -> Dict:
        """Get table schema information"""
        try:
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            columns = inspector.get_columns(table_name)
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": col.get("default"),
                    }
                    for col in columns
                ],
                "row_count": DatabaseConnector.get_row_count(connection_string, table_name)
            }
        except Exception as e:
            raise Exception(f"Failed to get table info: {str(e)}")
    
    @staticmethod
    def get_row_count(connection_string: str, table_name: str) -> int:
        """Get row count for a table"""
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.fetchone()[0]
        except:
            return 0
    
    @staticmethod
    def execute_query(connection_string: str, query: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        try:
            engine = create_engine(connection_string)
            
            # Add LIMIT clause if specified and not already present
            if limit and "limit" not in query.lower():
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    @staticmethod
    def fetch_table_data(
        connection_string: str, 
        table_name: str, 
        limit: int = 1000,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Fetch data from a table"""
        try:
            col_str = ", ".join(columns) if columns else "*"
            query = f"SELECT {col_str} FROM {table_name} LIMIT {limit}"
            return DatabaseConnector.execute_query(connection_string, query)
        except Exception as e:
            raise Exception(f"Failed to fetch table data: {str(e)}")
    
    @staticmethod
    def get_sample_data(connection_string: str, table_name: str, sample_size: int = 5) -> Dict:
        """Get sample data from table for preview"""
        try:
            df = DatabaseConnector.fetch_table_data(connection_string, table_name, limit=sample_size)
            return {
                "columns": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_rows": df.to_dict('records'),
                "total_rows": DatabaseConnector.get_row_count(connection_string, table_name)
            }
        except Exception as e:
            raise Exception(f"Failed to get sample data: {str(e)}")


def get_required_packages(db_type: str) -> List[str]:
    """Get required Python packages for database type"""
    packages = {
        'mysql': ['pymysql', 'cryptography'],
        'postgresql': ['psycopg2-binary'],
        'sqlite': [],  # Built-in
        'sqlserver': ['pyodbc'],
        'oracle': ['cx_oracle']
    }
    return packages.get(db_type.lower(), [])
