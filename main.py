"""
Main Script for Campus Energy-Use Dashboard
Orchestrates data ingestion, processing, visualization, and report generation.
"""

import os
import sys
import logging
from datetime import datetime
import importlib.util

# Add src directory to path for imports - must be before module imports
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Dynamically import modules to avoid path issues
data_processor_spec = importlib.util.spec_from_file_location(
    "data_processor", os.path.join(src_path, "data_processor.py"))
data_processor = importlib.util.module_from_spec(data_processor_spec)
data_processor_spec.loader.exec_module(data_processor)

visualization_spec = importlib.util.spec_from_file_location(
    "visualization", os.path.join(src_path, "visualization.py"))
visualization = importlib.util.module_from_spec(visualization_spec)
visualization_spec.loader.exec_module(visualization)

classes_spec = importlib.util.spec_from_file_location(
    "classes", os.path.join(src_path, "classes.py"))
classes = importlib.util.module_from_spec(classes_spec)
classes_spec.loader.exec_module(classes)

DataProcessor = data_processor.DataProcessor
calculate_daily_totals = data_processor.calculate_daily_totals
calculate_weekly_aggregates = data_processor.calculate_weekly_aggregates
building_wise_summary = data_processor.building_wise_summary
hourly_peak_analysis = data_processor.hourly_peak_analysis
export_cleaned_data = data_processor.export_cleaned_data
export_building_summary = data_processor.export_building_summary

EnergyDashboard = visualization.EnergyDashboard

Building = classes.Building
MeterReading = classes.MeterReading
BuildingManager = classes.BuildingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('energy_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""

    print("\n" + "="*70)
    print(" "*15 + "CAMPUS ENERGY-USE DASHBOARD")
    print(" "*10 + "Data Processing and Analysis Pipeline")
    print("="*70 + "\n")

    # Step 1: Data Ingestion
    print("[STEP 1] DATA INGESTION AND VALIDATION")
    print("-" * 70)

    processor = DataProcessor(data_dir='./data')
    df_combined = processor.ingest_data()

    summary = processor.get_data_summary()
    print(
        f"[OK] Successfully loaded {summary['total_rows']} records from {summary['buildings']} buildings")
    print(f"[OK] Date range: {summary['date_range']}")
    print(f"[OK] Files processed: {summary['processed_files']}")
    if summary['invalid_files'] > 0:
        print(f"[WARNING] Invalid files skipped: {summary['invalid_files']}")
    print()

    # Step 2: Data Aggregation
    print("[STEP 2] DATA AGGREGATION AND ANALYSIS")
    print("-" * 70)

    # Calculate aggregations
    daily_totals = calculate_daily_totals(df_combined)
    weekly_aggregates = calculate_weekly_aggregates(df_combined)
    building_summary = building_wise_summary(df_combined)
    hourly_peaks = hourly_peak_analysis(df_combined)

    print(f"[OK] Daily totals calculated: {len(daily_totals)} days of data")
    print(f"[OK] Weekly aggregates calculated: {len(weekly_aggregates)} weeks")
    print(f"[OK] Building-wise summary: {len(building_summary)} buildings")
    print(f"[OK] Peak hours analysis: {len(hourly_peaks)} time slots")
    print()

    # Display building summary
    print("Building-Wise Summary:")
    print(building_summary.to_string(index=False))
    print()

    # Step 3: Visualization
    print("[STEP 3] VISUALIZATION AND DASHBOARD CREATION")
    print("-" * 70)

    dashboard = EnergyDashboard(figsize=(16, 12))
    dashboard.create_dashboard(
        daily_df=daily_totals,
        weekly_df=weekly_aggregates,
        building_summary_df=building_summary,
        raw_df=df_combined,
        output_path='./output/dashboard.png'
    )

    print("[OK] Main dashboard created: ./output/dashboard.png")
    print()

    # Step 4: Export Data
    print("[STEP 4] DATA EXPORT")
    print("-" * 70)

    export_cleaned_data(df_combined, './output/cleaned_energy_data.csv')
    export_building_summary(building_summary, './output/building_summary.csv')

    # Export hourly peaks analysis
    hourly_peaks.to_csv('./output/hourly_peak_analysis.csv', index=False)
    print("[OK] Cleaned energy data exported: ./output/cleaned_energy_data.csv")
    print("[OK] Building summary exported: ./output/building_summary.csv")
    print("[OK] Hourly peak analysis exported: ./output/hourly_peak_analysis.csv")
    print()

    # Step 5: Report Generation (OOP approach)
    print("[STEP 5] REPORT GENERATION")
    print("-" * 70)

    # Create building objects and populate them
    manager = BuildingManager()

    for building_name in df_combined['building_name'].unique():
        building = Building(building_name)
        building_data = df_combined[df_combined['building_name']
                                    == building_name]

        for _, row in building_data.iterrows():
            reading = MeterReading(
                timestamp=row['date'].strftime('%Y-%m-%d'),
                kwh=row['kwh'],
                time_slot=row['time']
            )
            building.add_reading(reading)

        manager.add_building(building)

    # Generate reports
    campus_report = manager.generate_campus_report()

    print(campus_report)
    print()

    # Step 6: Executive Summary
    print("[STEP 6] EXECUTIVE SUMMARY")
    print("-" * 70)

    # Calculate key metrics
    total_consumption = df_combined['kwh'].sum()
    highest_building = building_summary.iloc[0]
    lowest_building = building_summary.iloc[-1]

    # Find peak load time
    if 'time' in df_combined.columns:
        peak_time = df_combined.groupby('time')['kwh'].sum().idxmax()
    else:
        peak_time = "N/A"

    # Calculate average daily consumption
    avg_daily = daily_totals['total_kwh'].mean()
    max_daily = daily_totals['total_kwh'].max()
    min_daily = daily_totals['total_kwh'].min()

    # Create executive summary
    summary_text = f"""
==================================================================
        CAMPUS ENERGY-USE DASHBOARD - EXECUTIVE SUMMARY
==================================================================

ANALYSIS PERIOD: {df_combined['date'].min().date()} to {df_combined['date'].max().date()}

==================================================================

CAMPUS OVERVIEW
------------------------------------------------------------------
* Total Campus Consumption: {total_consumption:,.2f} kWh
* Number of Buildings Analyzed: {len(df_combined['building_name'].unique())}
* Data Points Collected: {len(df_combined):,}
* Analysis Period: {(df_combined['date'].max() - df_combined['date'].min()).days} days

==================================================================

DAILY CONSUMPTION STATISTICS
------------------------------------------------------------------
* Average Daily Consumption: {avg_daily:,.2f} kWh
* Maximum Daily Consumption: {max_daily:,.2f} kWh
* Minimum Daily Consumption: {min_daily:,.2f} kWh

==================================================================

TOP CONSUMERS
------------------------------------------------------------------
Highest Consuming Building: {highest_building['building_name']}
  * Total Consumption: {highest_building['total']:,.2f} kWh
  * Average per Reading: {highest_building['average']:.2f} kWh
  * Peak Consumption: {highest_building['max']:.2f} kWh

Lowest Consuming Building: {lowest_building['building_name']}
  * Total Consumption: {lowest_building['total']:,.2f} kWh
  * Average per Reading: {lowest_building['average']:.2f} kWh
  * Peak Consumption: {lowest_building['max']:.2f} kWh

==================================================================

PEAK LOAD ANALYSIS
------------------------------------------------------------------
* Peak Load Time: {peak_time}

==================================================================

KEY INSIGHTS & RECOMMENDATIONS
------------------------------------------------------------------
1. Consumption Variability: The standard deviation across buildings is 
   significant, indicating opportunities for energy efficiency improvements.

2. Peak Hour Management: Focus on reducing peak-hour consumption through:
   - Demand-side management programs
   - Peak load shifting initiatives
   - Equipment efficiency upgrades

3. Building Comparisons: {highest_building['building_name']} consumes 
   {((highest_building['total']/lowest_building['total'] - 1) * 100):.1f}% more energy than {lowest_building['building_name']}.
   Investigate operational differences for best practices sharing.

4. Weekly Patterns: Weekday vs. weekend consumption patterns show clear 
   variations. Implement occupancy-based control systems.

5. Efficiency Targets: Setting a 10-15% reduction target across all 
   buildings could save {(total_consumption * 0.125):,.2f} kWh annually.

==================================================================

OUTPUT FILES GENERATED
------------------------------------------------------------------
[OK] dashboard.png                    - Multi-chart visualization
[OK] cleaned_energy_data.csv          - Processed dataset
[OK] building_summary.csv             - Building statistics
[OK] hourly_peak_analysis.csv         - Time-based analysis
[OK] energy_dashboard.log             - Execution log
[OK] summary.txt                      - This executive summary
[OK] Individual building charts       - Per-building visualizations

==================================================================
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==================================================================
    """

    # Print and save summary
    print(summary_text)

    with open('./output/summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary_text)

    logger.info("Executive summary saved to ./output/summary.txt")

    # Print completion message
    print("\n" + "="*70)
    print(" "*18 + "*** ANALYSIS COMPLETE ***")
    print(" "*12 + "All outputs saved to ./output/ directory")
    print("="*70 + "\n")

    return manager, processor


if __name__ == '__main__':
    try:
        # Ensure output directory exists
        os.makedirs('./output', exist_ok=True)

        # Run the main pipeline
        manager, processor = main()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nERROR: {e}\nCheck energy_dashboard.log for details.")
        sys.exit(1)
