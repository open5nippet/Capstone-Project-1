"""
Data Ingestion and Processing Module for Campus Energy Dashboard
Handles reading, validating, and aggregating energy consumption data.
"""

import os
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Handles data ingestion, validation, and aggregation."""

    def __init__(self, data_dir: str = './data'):
        """
        Initialize the data processor.

        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        self.df_combined = None
        self.invalid_files = []
        self.processed_files = []

    def find_csv_files(self) -> List[Path]:
        """
        Find all CSV files in the data directory.

        Returns:
            List of Path objects for CSV files
        """
        try:
            csv_files = list(self.data_dir.glob('*.csv'))
            logger.info(f"Found {len(csv_files)} CSV files in {self.data_dir}")
            return csv_files
        except Exception as e:
            logger.error(f"Error finding CSV files: {e}")
            return []

    def read_and_validate_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Read a CSV file with error handling.

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame if successful, None if file is invalid
        """
        try:
            # Attempt to read the CSV file
            df = pd.read_csv(file_path, on_bad_lines='skip')

            # Validate required columns
            required_columns = ['date', 'kwh']
            if not all(col in df.columns for col in required_columns):
                logger.warning(
                    f"File {file_path.name} missing required columns. "
                    f"Expected: {required_columns}, Got: {list(df.columns)}"
                )
                self.invalid_files.append(file_path.name)
                return None

            # Check for empty data
            if df.empty:
                logger.warning(f"File {file_path.name} is empty")
                self.invalid_files.append(file_path.name)
                return None

            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

            # Remove rows with invalid dates
            invalid_dates = df['date'].isna().sum()
            if invalid_dates > 0:
                logger.warning(
                    f"File {file_path.name}: {invalid_dates} invalid dates removed")
                df = df[df['date'].notna()]

            # Convert kwh to numeric
            df['kwh'] = pd.to_numeric(df['kwh'], errors='coerce')

            # Remove rows with invalid kWh values
            invalid_kwh = df['kwh'].isna().sum()
            if invalid_kwh > 0:
                logger.warning(
                    f"File {file_path.name}: {invalid_kwh} invalid kWh values removed")
                df = df[df['kwh'].notna()]

            # Ensure building_name exists
            if 'building_name' not in df.columns:
                # Extract building name from filename
                building_name = file_path.stem.replace('_', ' ').title()
                df['building_name'] = building_name
                logger.info(
                    f"Added building_name '{building_name}' to {file_path.name}")

            logger.info(f"Successfully read {file_path.name} ({len(df)} rows)")
            self.processed_files.append(file_path.name)
            return df

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            self.invalid_files.append(file_path.name)
            return None
        except Exception as e:
            logger.error(f"Error reading {file_path.name}: {e}")
            self.invalid_files.append(file_path.name)
            return None

    def ingest_data(self) -> pd.DataFrame:
        """
        Read and combine all CSV files.

        Returns:
            Combined DataFrame with all building data
        """
        csv_files = self.find_csv_files()
        dataframes = []

        for file_path in csv_files:
            df = self.read_and_validate_csv(file_path)
            if df is not None:
                dataframes.append(df)

        if not dataframes:
            logger.error("No valid data files found!")
            self.df_combined = pd.DataFrame()
            return self.df_combined

        # Combine all dataframes
        self.df_combined = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Combined data: {len(self.df_combined)} total rows")

        return self.df_combined

    def get_data_summary(self) -> Dict:
        """Get summary statistics of the loaded data."""
        if self.df_combined is None or self.df_combined.empty:
            return {}

        return {
            'total_rows': len(self.df_combined),
            'buildings': self.df_combined['building_name'].nunique(),
            'date_range': f"{self.df_combined['date'].min().date()} to {self.df_combined['date'].max().date()}",
            'total_consumption': self.df_combined['kwh'].sum(),
            'processed_files': len(self.processed_files),
            'invalid_files': len(self.invalid_files)
        }


def calculate_daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily total consumption.

    Args:
        df: DataFrame with 'date' and 'kwh' columns

    Returns:
        DataFrame with date and daily total
    """
    if df.empty:
        return pd.DataFrame()

    daily = df.groupby('date')['kwh'].sum().reset_index()
    daily.columns = ['date', 'total_kwh']
    return daily.sort_values('date')


def calculate_weekly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate weekly total consumption.

    Args:
        df: DataFrame with 'date' and 'kwh' columns

    Returns:
        DataFrame with week start date and weekly total
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df['week_start'] = df['date'] - \
        pd.to_timedelta(df['date'].dt.dayofweek, unit='d')
    weekly = df.groupby('week_start')['kwh'].sum().reset_index()
    weekly.columns = ['week_start', 'total_kwh']
    return weekly.sort_values('week_start')


def building_wise_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate summary statistics per building.

    Args:
        df: DataFrame with 'building_name' and 'kwh' columns

    Returns:
        DataFrame with building statistics
    """
    if df.empty:
        return pd.DataFrame()

    summary = df.groupby('building_name')['kwh'].agg([
        ('total', 'sum'),
        ('average', 'mean'),
        ('min', 'min'),
        ('max', 'max'),
        ('std_dev', 'std'),
        ('count', 'count')
    ]).reset_index()

    summary = summary.round(2)
    return summary.sort_values('total', ascending=False)


def hourly_peak_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze peak consumption by time of day.

    Args:
        df: DataFrame with 'time' and 'kwh' columns

    Returns:
        DataFrame with hourly analysis
    """
    if df.empty or 'time' not in df.columns:
        return pd.DataFrame()

    hourly = df.groupby('time')['kwh'].agg([
        ('average', 'mean'),
        ('peak', 'max'),
        ('minimum', 'min'),
        ('count', 'count')
    ]).reset_index()

    return hourly.round(2).sort_values('average', ascending=False)


def export_cleaned_data(df: pd.DataFrame, output_path: str = './output/cleaned_energy_data.csv'):
    """
    Export cleaned data to CSV.

    Args:
        df: DataFrame to export
        output_path: Output file path
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data exported to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting cleaned data: {e}")


def export_building_summary(summary_df: pd.DataFrame, output_path: str = './output/building_summary.csv'):
    """
    Export building summary to CSV.

    Args:
        summary_df: Summary DataFrame
        output_path: Output file path
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        summary_df.to_csv(output_path, index=False)
        logger.info(f"Building summary exported to {output_path}")
    except Exception as e:
        logger.error(f"Error exporting building summary: {e}")
