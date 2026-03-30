"""
CSV Processing Flow

Background task flow for processing and analyzing CSV files.
Performs heavy data analysis operations using pandas, numpy, and scikit-learn.
"""

import os
import io
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List

from prefect import flow, task, get_run_logger
# Note: artifacts API changed in Prefect 3.x - using logging instead

# Import data science libraries
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats


@task(name="Load CSV File", retries=2, retry_delay_seconds=5)
def load_csv_task(file_path: str) -> pd.DataFrame:
    """Load CSV file with multiple encoding fallbacks"""
    logger = get_run_logger()
    logger.info(f"Loading CSV file: {file_path}")
    
    # Try multiple encodings
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logger.info(f"Successfully loaded CSV with encoding: {encoding}")
            logger.info(f"Shape: {df.shape}")
            return df
        except Exception as e:
            logger.warning(f"Failed with encoding {encoding}: {str(e)}")
            continue
    
    raise ValueError(f"Could not load CSV file with any encoding: {file_path}")


@task(name="Clean Data")
def clean_data_task(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the dataframe - handle missing values, fix types"""
    logger = get_run_logger()
    logger.info("Cleaning data...")
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col].fillna(df[col].median(), inplace=True)
    
    # Convert string columns that should be numeric
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = df[col].str.replace(',', '').astype(float)
                logger.info(f"Converted column '{col}' to numeric")
            except (ValueError, AttributeError):
                pass  # Keep as string if conversion fails
    
    logger.info(f"Data cleaned. Shape: {df.shape}")
    return df


@task(name="Generate Summary Statistics")
def generate_summary_task(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics for the dataframe"""
    logger = get_run_logger()
    logger.info("Generating summary statistics...")
    
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
        "categorical_columns": list(df.select_dtypes(include=['object']).columns),
        "missing_values": df.isnull().sum().to_dict(),
        "basic_stats": df.describe().to_dict()
    }
    
    logger.info(f"Summary generated for {len(df)} rows, {len(df.columns)} columns")
    return summary


@task(name="Generate Visualization")
def generate_visualization_task(df: pd.DataFrame, viz_type: str = "histogram", 
                                column: Optional[str] = None) -> Optional[str]:
    """Generate matplotlib visualization and return as base64"""
    logger = get_run_logger()
    
    try:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            logger.warning("No numeric columns found for visualization")
            return None
        
        # Default to first numeric column if none specified
        if column is None:
            column = numeric_cols[0]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if viz_type == "histogram":
            ax.hist(df[column].dropna(), bins=30, color='skyblue', edgecolor='black')
            ax.set_title(f"Distribution of {column}")
            ax.set_xlabel(column)
            ax.set_ylabel("Frequency")
            
        elif viz_type == "boxplot":
            ax.boxplot(df[column].dropna(), vert=True)
            ax.set_title(f"Box Plot of {column}")
            ax.set_ylabel(column)
            
        elif viz_type == "heatmap":
            numeric_df = df[numeric_cols].head(20)
            sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt='.2f', ax=ax)
            ax.set_title("Correlation Heatmap")
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)
        
        logger.info(f"Generated {viz_type} visualization for {column}")
        return img_base64
        
    except Exception as e:
        logger.error(f"Failed to generate visualization: {str(e)}")
        return None


@task(name="Run Analysis")
def run_analysis_task(df: pd.DataFrame, analysis_type: str, 
                      params: Optional[Dict] = None) -> Dict[str, Any]:
    """Run specific analysis based on type"""
    logger = get_run_logger()
    logger.info(f"Running {analysis_type} analysis...")
    
    params = params or {}
    result = {"analysis_type": analysis_type, "success": False}
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    try:
        if analysis_type == "correlation":
            corr_matrix = df[numeric_cols].corr()
            result["correlation_matrix"] = corr_matrix.to_dict()
            result["success"] = True
            
        elif analysis_type == "regression":
            # Simple linear regression
            target = params.get("target", numeric_cols[0])
            feature = params.get("feature", numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0])
            
            X = df[[feature]].dropna()
            y = df.loc[X.index, target]
            
            if len(X) > 10:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                model = LinearRegression()
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                result["coefficient"] = model.coef_[0] if len(model.coef_) > 0 else 0
                result["intercept"] = model.intercept_
                result["r2_score"] = r2_score(y_test, y_pred)
                result["rmse"] = np.sqrt(mean_squared_error(y_test, y_pred))
                result["success"] = True
                
        elif analysis_type == "outliers":
            # Detect outliers using IQR
            outliers_info = {}
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                outliers_info[col] = {
                    "count": len(outliers),
                    "percentage": len(outliers) / len(df) * 100,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound
                }
            result["outliers"] = outliers_info
            result["success"] = True
            
        elif analysis_type == "distribution":
            dist_info = {}
            for col in numeric_cols[:5]:  # Limit to first 5 columns
                data = df[col].dropna()
                if len(data) > 3:
                    skewness = stats.skew(data)
                    kurtosis = stats.kurtosis(data)
                    dist_info[col] = {
                        "skewness": float(skewness),
                        "kurtosis": float(kurtosis),
                        "mean": float(data.mean()),
                        "median": float(data.median()),
                        "std": float(data.std())
                    }
            result["distribution"] = dist_info
            result["success"] = True
            
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        result["error"] = str(e)
    
    return result


@flow(name="Process CSV File", log_prints=True)
def process_csv_file(
    file_path: str,
    analysis_type: Optional[str] = None,
    viz_type: Optional[str] = "histogram",
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Main flow for processing CSV files.
    
    Args:
        file_path: Path to the CSV file
        analysis_type: Type of analysis to perform (correlation, regression, outliers, distribution)
        viz_type: Type of visualization (histogram, boxplot, heatmap)
        params: Additional parameters for analysis
    
    Returns:
        Dictionary containing processing results
    """
    logger = get_run_logger()
    logger.info(f"Starting CSV processing for: {file_path}")
    
    results = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "success": False
    }
    
    try:
        # Step 1: Load the CSV
        df = load_csv_task(file_path)
        
        # Step 2: Clean the data
        df = clean_data_task(df)
        
        # Step 3: Generate summary
        summary = generate_summary_task(df)
        results["summary"] = summary
        
        # Step 4: Generate visualization if requested
        if viz_type:
            viz_base64 = generate_visualization_task(df, viz_type)
            if viz_base64:
                results["visualization"] = f"data:image/png;base64,{viz_base64}"
        
        # Step 5: Run analysis if requested
        if analysis_type:
            analysis_result = run_analysis_task(df, analysis_type, params)
            results["analysis"] = analysis_result
        
        results["success"] = True
        logger.info("CSV processing completed successfully")
        
    except Exception as e:
        logger.error(f"CSV processing failed: {str(e)}")
        results["error"] = str(e)
        results["success"] = False
    
    return results


# Alternative entry point for batch processing
@flow(name="Process Multiple CSV Files")
def process_multiple_csvs(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Process multiple CSV files"""
    results = []
    for file_path in file_paths:
        result = process_csv_file(file_path)
        results.append(result)
    return results

