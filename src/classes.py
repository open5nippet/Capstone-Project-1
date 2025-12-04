"""
Object-Oriented Models for Campus Energy-Use Dashboard
Defines Building, MeterReading, and BuildingManager classes.
"""

from datetime import datetime
from typing import List, Dict
import statistics


class MeterReading:
    """Represents a single meter reading at a specific timestamp."""

    def __init__(self, timestamp: str, kwh: float, time_slot: str = None):
        """
        Initialize a meter reading.

        Args:
            timestamp: Date in format 'YYYY-MM-DD'
            kwh: Energy consumption in kilowatt-hours
            time_slot: Time of day (e.g., '08:00', '12:00')
        """
        self.timestamp = datetime.strptime(timestamp, '%Y-%m-%d')
        self.kwh = float(kwh)
        self.time_slot = time_slot

    def __repr__(self):
        return f"MeterReading({self.timestamp.date()}, {self.kwh} kWh)"


class Building:
    """Represents a campus building with meter readings and consumption analytics."""

    def __init__(self, name: str):
        """
        Initialize a building.

        Args:
            name: Name of the building
        """
        self.name = name
        self.meter_readings: List[MeterReading] = []

    def add_reading(self, reading: MeterReading):
        """Add a meter reading to the building."""
        self.meter_readings.append(reading)

    def calculate_total_consumption(self) -> float:
        """Calculate total energy consumption across all readings."""
        return sum(reading.kwh for reading in self.meter_readings)

    def calculate_average_consumption(self) -> float:
        """Calculate average energy consumption per reading."""
        if not self.meter_readings:
            return 0.0
        return self.calculate_total_consumption() / len(self.meter_readings)

    def calculate_peak_consumption(self) -> float:
        """Calculate peak (maximum) energy consumption."""
        if not self.meter_readings:
            return 0.0
        return max(reading.kwh for reading in self.meter_readings)

    def calculate_min_consumption(self) -> float:
        """Calculate minimum energy consumption."""
        if not self.meter_readings:
            return 0.0
        return min(reading.kwh for reading in self.meter_readings)

    def calculate_std_dev(self) -> float:
        """Calculate standard deviation of consumption."""
        if len(self.meter_readings) < 2:
            return 0.0
        kwh_values = [reading.kwh for reading in self.meter_readings]
        return statistics.stdev(kwh_values)

    def get_daily_consumption(self) -> Dict[str, float]:
        """
        Group meter readings by day and calculate daily totals.

        Returns:
            Dictionary with date as key and total kWh as value
        """
        daily_totals = {}
        for reading in self.meter_readings:
            date_key = reading.timestamp.strftime('%Y-%m-%d')
            daily_totals[date_key] = daily_totals.get(
                date_key, 0) + reading.kwh
        return daily_totals

    def get_hourly_breakdown(self, date: str) -> Dict[str, float]:
        """
        Get hourly breakdown for a specific date.

        Args:
            date: Date in format 'YYYY-MM-DD'

        Returns:
            Dictionary with time slot as key and kWh as value
        """
        hourly_data = {}
        for reading in self.meter_readings:
            if reading.timestamp.strftime('%Y-%m-%d') == date:
                hourly_data[reading.time_slot] = reading.kwh
        return hourly_data

    def generate_report(self) -> str:
        """Generate a text report with building statistics."""
        total = self.calculate_total_consumption()
        avg = self.calculate_average_consumption()
        peak = self.calculate_peak_consumption()
        minimum = self.calculate_min_consumption()
        std_dev = self.calculate_std_dev()

        report = f"""
        ========================================
        BUILDING: {self.name}
        ========================================
        Total Readings: {len(self.meter_readings)}
        Total Consumption: {total:.2f} kWh
        Average Consumption: {avg:.2f} kWh/reading
        Peak Consumption: {peak:.2f} kWh
        Minimum Consumption: {minimum:.2f} kWh
        Standard Deviation: {std_dev:.2f} kWh
        ========================================
        """
        return report

    def __repr__(self):
        return f"Building({self.name}, {len(self.meter_readings)} readings)"


class BuildingManager:
    """Manages multiple buildings and campus-wide analytics."""

    def __init__(self):
        """Initialize the building manager."""
        self.buildings: Dict[str, Building] = {}

    def add_building(self, building: Building):
        """Add a building to the manager."""
        self.buildings[building.name] = building

    def get_building(self, name: str) -> Building:
        """Retrieve a building by name."""
        return self.buildings.get(name)

    def calculate_campus_total(self) -> float:
        """Calculate total energy consumption across all buildings."""
        return sum(
            building.calculate_total_consumption()
            for building in self.buildings.values()
        )

    def get_highest_consumer(self) -> tuple:
        """
        Identify the building with highest total consumption.

        Returns:
            Tuple of (building_name, total_consumption)
        """
        if not self.buildings:
            return None, 0.0

        highest = max(
            self.buildings.items(),
            key=lambda item: item[1].calculate_total_consumption()
        )
        return highest[0], highest[1].calculate_total_consumption()

    def get_lowest_consumer(self) -> tuple:
        """
        Identify the building with lowest total consumption.

        Returns:
            Tuple of (building_name, total_consumption)
        """
        if not self.buildings:
            return None, 0.0

        lowest = min(
            self.buildings.items(),
            key=lambda item: item[1].calculate_total_consumption()
        )
        return lowest[0], lowest[1].calculate_total_consumption()

    def get_summary_table(self) -> Dict[str, Dict]:
        """
        Generate summary statistics for all buildings.

        Returns:
            Dictionary with building names as keys and stats dicts as values
        """
        summary = {}
        for name, building in self.buildings.items():
            summary[name] = {
                'total': building.calculate_total_consumption(),
                'average': building.calculate_average_consumption(),
                'peak': building.calculate_peak_consumption(),
                'minimum': building.calculate_min_consumption(),
                'std_dev': building.calculate_std_dev(),
                'readings': len(building.meter_readings)
            }
        return summary

    def generate_campus_report(self) -> str:
        """Generate a comprehensive campus-wide report."""
        campus_total = self.calculate_campus_total()
        highest_name, highest_value = self.get_highest_consumer()
        lowest_name, lowest_value = self.get_lowest_consumer()

        report = f"""
        ========================================
        CAMPUS-WIDE ENERGY SUMMARY
        ========================================
        Total Buildings: {len(self.buildings)}
        Campus Total Consumption: {campus_total:.2f} kWh
        
        Highest Consumer: {highest_name}
        - Consumption: {highest_value:.2f} kWh
        
        Lowest Consumer: {lowest_name}
        - Consumption: {lowest_value:.2f} kWh
        
        Percentage Distribution:
        """

        for name, building in sorted(self.buildings.items()):
            total = building.calculate_total_consumption()
            percentage = (total / campus_total *
                          100) if campus_total > 0 else 0
            report += f"\n        {name}: {percentage:.1f}% ({total:.2f} kWh)"

        report += "\n        ========================================"
        return report

    def __repr__(self):
        return f"BuildingManager({len(self.buildings)} buildings)"
