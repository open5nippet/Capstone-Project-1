"""
Visualization Module for Campus Energy Dashboard
Creates charts and multi-plot dashboards using Matplotlib.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import logging
import os
from typing import Tuple

logger = logging.getLogger(__name__)


class EnergyDashboard:
    """Creates multi-chart visualizations for energy consumption analysis."""

    def __init__(self, figsize: Tuple[int, int] = (16, 12)):
        """
        Initialize the dashboard creator.

        Args:
            figsize: Figure size as (width, height)
        """
        self.figsize = figsize
        self.fig = None
        self.axes = None

    def create_trend_line(self, ax, daily_df: pd.DataFrame, title: str = 'Daily Energy Consumption Trend'):
        """
        Create a trend line plot for daily consumption.

        Args:
            ax: Matplotlib axis object
            daily_df: DataFrame with 'date' and 'total_kwh' columns
            title: Plot title
        """
        if daily_df.empty:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return

        ax.plot(daily_df['date'], daily_df['total_kwh'],
                marker='o', linewidth=2, markersize=6, color='#2E86AB', label='Daily Total')

        # Add trend line
        z = np.polyfit(range(len(daily_df)), daily_df['total_kwh'], 2)
        p = np.poly1d(z)
        ax.plot(daily_df['date'], p(range(len(daily_df))),
                "--", color='#A23B72', linewidth=2, label='Trend', alpha=0.7)

        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel('Energy Consumption (kWh)',
                      fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', fontsize=10)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def create_building_comparison(self, ax, building_summary_df: pd.DataFrame,
                                   title: str = 'Average Weekly Usage by Building'):
        """
        Create a bar chart comparing buildings.

        Args:
            ax: Matplotlib axis object
            building_summary_df: DataFrame with building stats
            title: Plot title
        """
        if building_summary_df.empty:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return

        # Use average consumption for comparison
        buildings = building_summary_df['building_name'].tolist()
        averages = building_summary_df['average'].tolist()

        colors = ['#F18F01', '#C73E1D', '#6A994E', '#2E86AB', '#A23B72']
        colors = colors[:len(buildings)]

        bars = ax.bar(buildings, averages, color=colors,
                      edgecolor='black', linewidth=1.2, alpha=0.8)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_ylabel('Average Consumption (kWh)',
                      fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def create_building_distribution(self, ax, building_summary_df: pd.DataFrame,
                                     title: str = 'Total Energy Consumption Distribution'):
        """
        Create a pie chart showing energy distribution.

        Args:
            ax: Matplotlib axis object
            building_summary_df: DataFrame with building stats
            title: Plot title
        """
        if building_summary_df.empty:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return

        buildings = building_summary_df['building_name'].tolist()
        totals = building_summary_df['total'].tolist()

        colors = ['#F18F01', '#C73E1D', '#6A994E', '#2E86AB', '#A23B72']
        colors = colors[:len(buildings)]

        wedges, texts, autotexts = ax.pie(
            totals,
            labels=buildings,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )

        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)

    def create_peak_hours_analysis(self, ax, df: pd.DataFrame,
                                   title: str = 'Peak Hour Analysis by Building'):
        """
        Create scatter plot of peak consumption vs building.

        Args:
            ax: Matplotlib axis object
            df: Raw data DataFrame with 'time', 'kwh', and 'building_name'
            title: Plot title
        """
        if df.empty or 'time' not in df.columns:
            ax.text(0.5, 0.5, 'No hourly data available',
                    ha='center', va='center')
            return

        # Get unique buildings and times
        buildings = df['building_name'].unique()
        times = sorted(df['time'].unique())

        colors_dict = {'Admin Building': '#2E86AB', 'Science Lab': '#F18F01',
                       'Library': '#6A994E', 'Dormitory': '#A23B72', 'Sports Complex': '#C73E1D'}

        for building in buildings:
            building_data = df[df['building_name'] == building]
            time_indices = [times.index(
                t) if t in times else 0 for t in building_data['time']]

            color = colors_dict.get(building, '#2E86AB')
            ax.scatter(time_indices, building_data['kwh'],
                       label=building, s=80, alpha=0.7, color=color, edgecolor='black', linewidth=0.5)

        ax.set_xlabel('Time Slot', fontsize=11, fontweight='bold')
        ax.set_ylabel('Consumption (kWh)', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.set_xticks(range(len(times)))
        ax.set_xticklabels(times, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', fontsize=9)

    def create_weekly_comparison(self, ax, weekly_df: pd.DataFrame,
                                 title: str = 'Weekly Energy Consumption'):
        """
        Create a line and area plot for weekly consumption.

        Args:
            ax: Matplotlib axis object
            weekly_df: DataFrame with 'week_start' and 'total_kwh'
            title: Plot title
        """
        if weekly_df.empty:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return

        ax.fill_between(weekly_df['week_start'], weekly_df['total_kwh'],
                        alpha=0.3, color='#6A994E', label='Weekly Consumption')
        ax.plot(weekly_df['week_start'], weekly_df['total_kwh'],
                marker='s', linewidth=2.5, markersize=7, color='#6A994E', label='Weekly Total')

        ax.set_xlabel('Week Starting', fontsize=11, fontweight='bold')
        ax.set_ylabel('Energy Consumption (kWh)',
                      fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', fontsize=10)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def create_dashboard(self, daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                         building_summary_df: pd.DataFrame, raw_df: pd.DataFrame,
                         output_path: str = './output/dashboard.png'):
        """
        Create a comprehensive dashboard with multiple visualizations.

        Args:
            daily_df: Daily consumption DataFrame
            weekly_df: Weekly consumption DataFrame
            building_summary_df: Building summary statistics
            raw_df: Raw data with hourly breakdowns
            output_path: Path to save the dashboard image
        """
        self.fig, self.axes = plt.subplots(2, 3, figsize=self.figsize)
        self.fig.suptitle('Campus Energy-Use Dashboard',
                          fontsize=16, fontweight='bold', y=0.995)

        # Flatten axes for easier indexing
        axes_flat = self.axes.flatten()

        # Plot 1: Daily Trend
        self.create_trend_line(axes_flat[0], daily_df)

        # Plot 2: Building Comparison
        self.create_building_comparison(axes_flat[1], building_summary_df)

        # Plot 3: Distribution Pie Chart
        self.create_building_distribution(axes_flat[2], building_summary_df)

        # Plot 4: Weekly Comparison
        self.create_weekly_comparison(axes_flat[3], weekly_df)

        # Plot 5: Peak Hours Analysis
        self.create_peak_hours_analysis(axes_flat[4], raw_df)

        # Plot 6: Building Statistics Table
        self.create_stats_table(axes_flat[5], building_summary_df)

        # Adjust layout
        plt.tight_layout()

        # Save figure
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Dashboard saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving dashboard: {e}")

        return self.fig, self.axes

    def create_stats_table(self, ax, building_summary_df: pd.DataFrame):
        """
        Create a table visualization of building statistics.

        Args:
            ax: Matplotlib axis object
            building_summary_df: DataFrame with building statistics
        """
        ax.axis('tight')
        ax.axis('off')

        if building_summary_df.empty:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return

        # Prepare table data
        table_data = building_summary_df[[
            'building_name', 'total', 'average', 'max', 'min']].copy()
        table_data.columns = ['Building', 'Total', 'Avg', 'Peak', 'Min']

        # Round values
        for col in ['Total', 'Avg', 'Peak', 'Min']:
            table_data[col] = table_data[col].round(2)

        # Create table
        table = ax.table(cellText=table_data.values,
                         colLabels=table_data.columns,
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.25, 0.15, 0.15, 0.15, 0.15])

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        # Style header
        for i in range(len(table_data.columns)):
            table[(0, i)].set_facecolor('#2E86AB')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # Alternate row colors
        for i in range(1, len(table_data) + 1):
            for j in range(len(table_data.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F0F0F0')
                else:
                    table[(i, j)].set_facecolor('white')

        ax.set_title('Building Statistics Summary',
                     fontsize=13, fontweight='bold', pad=15)

    def show(self):
        """Display the dashboard."""
        if self.fig:
            plt.show()
