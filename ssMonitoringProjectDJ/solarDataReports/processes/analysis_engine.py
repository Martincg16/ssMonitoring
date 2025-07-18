"""
Analysis Engine for Solar Data Reports
Handles analysis of solar system data to detect anomalies and issues
"""

from datetime import datetime, date, timedelta
from django.db.models import Avg, StdDev, Count
from .query_engine import SolarDataQuery

class SolarDataAnalysis:
    """
    Main analysis engine for solar data reports
    Provides methods to analyze solar system data and detect issues
    """
    
    def __init__(self):
        self.query_engine = SolarDataQuery()

    def check_zero_production_system_single_day(self, check_date=None):
        """
        Checks which systems had zero or no production data for a specific date.
        If no date is provided, checks yesterday's data.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
        
        Output structure:
        {
            "date": str,                  # Date checked in ISO format
            "systems": [                  # List of systems with issues
                {
                    "id": int,           # System ID
                    "name": str,         # System name
                    "type": str          # "zero" (has 0 value) or "missing" (no data)
                },
                ...
            ]
        }
        """
        # Get the date to check
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        
        # Get production data for target date
        production_data = self.query_engine.get_systems_production(target_date, target_date)
        
        # Initialize result
        result = {
            "date": target_date.isoformat(),
            "systems": []
        }
        
        # Check each system's production
        for system_id, system_data in production_data['sistemas'].items():
            # Get target date's production data
            daily_data = system_data['produccion']['generacion_diaria']
            
            # If no data for target date
            if not daily_data:
                result["systems"].append({
                    "id": system_data['metadata']['id'],
                    "name": system_data['metadata']['nombre'],
                    "type": "missing"
                })
            # If data exists but shows zero production
            elif daily_data[0]['energia_kwh'] == 0:
                result["systems"].append({
                    "id": system_data['metadata']['id'],
                    "name": system_data['metadata']['nombre'],
                    "type": "zero"
                })
        
        return result

    def check_zero_production_inverter_single_day(self, check_date=None):
        """
        Checks which inverters had zero or no production data for a specific date.
        If no date is provided, checks yesterday's data.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
        
        Output structure:
        {
            "date": str,                  # Date checked in ISO format
            "inverters": [                # List of inverters with issues
                {
                    "id": int,           # Inverter ID
                    "name": str,         # System name (the inverter belongs to)
                    "type": str          # "zero" (has 0 value) or "missing" (no data)
                },
                ...
            ]
        }
        """
        # Get the date to check
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        
        # Get production data for target date
        production_data = self.query_engine.get_inverters_production(target_date, target_date)
        
        # Initialize result
        result = {
            "date": target_date.isoformat(),
            "inverters": []
        }
        
        # Check each inverter's production
        for inverter_id, inverter_data in production_data['inversores'].items():
            # Get target date's production data
            daily_data = inverter_data['produccion']['generacion_diaria']
            
            # If no data for target date
            if not daily_data:
                result["inverters"].append({
                    "id": inverter_data['metadata']['id'],
                    "name": inverter_data['metadata']['proyecto']['nombre'],
                    "type": "missing"
                })
            # If data exists but shows zero production
            elif daily_data[0]['energia_kwh'] == 0:
                result["inverters"].append({
                    "id": inverter_data['metadata']['id'],
                    "name": inverter_data['metadata']['proyecto']['nombre'],
                    "type": "zero"
                })
        
        return result

    def check_zero_production_granular_single_day(self, check_date=None):
        """
        Checks which granular devices had zero or no production data for a specific date.
        If no date is provided, checks yesterday's data.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
        
        Output structure:
        {
            "date": str,                  # Date checked in ISO format
            "devices": [                  # List of granular devices with issues
                {
                    "id": int,           # Granular device ID
                    "name": str,         # System name (the device belongs to)
                    "type": str          # "zero" (has 0 value) or "missing" (no data)
                },
                ...
            ]
        }
        """
        # Get the date to check
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        
        # Get production data for target date
        production_data = self.query_engine.get_granular_production(target_date, target_date)
        
        # Initialize result
        result = {
            "date": target_date.isoformat(),
            "devices": []
        }
        
        # Check each granular device's production
        for device_id, device_data in production_data['granular'].items():
            # Get target date's production data
            daily_data = device_data['produccion']['generacion_diaria']
            
            # If no data for target date
            if not daily_data:
                result["devices"].append({
                    "id": device_data['metadata']['id'],
                    "name": device_data['metadata']['proyecto']['nombre'],
                    "type": "missing"
                })
            # If data exists but shows zero production
            elif daily_data[0]['energia_kwh'] == 0:
                result["devices"].append({
                    "id": device_data['metadata']['id'],
                    "name": device_data['metadata']['proyecto']['nombre'],
                    "type": "zero"
                })
        
        return result 

    def check_production_deviation_systems(self, check_date=None, min_days_required=7, std_dev_threshold=1, days_to_compare=30):
        """
        Analyzes system production deviations by comparing a specific date against historical data.
        Only flags systems performing significantly below their historical average.
        Requires minimum number of days of historical data for reliable analysis.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
            min_days_required (int, optional): Minimum days of historical data required for analysis.
                                            Systems with less data will be skipped. Defaults to 7.
            std_dev_threshold (float, optional): Number of standard deviations to consider significant.
                                              Lower values catch more deviations. Defaults to 1.
            days_to_compare (int, optional): Number of past days to use for comparison. Defaults to 30.
        
        Output structure:
        {
            "date": str,                  # Date checked in ISO format
            "systems": [                  # List of systems performing below average
                {
                    "id": int,           # System ID
                    "name": str,         # System name
                    "current_kwh": float, # Current day's production
                    "avg_kwh": float,     # Average daily production
                    "std_dev": float,     # Standard deviation
                    "deviation": float,   # Number of standard deviations from mean
                    "percent_diff": float, # Percentage difference from mean (negative)
                    "days_analyzed": int  # Number of days used in analysis
                },
                ...
            ],
            "summary": {
                "total_systems": int,     # Total number of systems checked
                "systems_with_deviation": int,  # Number of systems with significant deviation
                "comparison_period": {
                    "start": str,         # ISO date
                    "end": str           # ISO date
                }
            }
        }
        """
        # Get the dates to analyze
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        start_date = target_date - timedelta(days=days_to_compare)
        
        # Get production data for all systems
        current_data = self.query_engine.get_systems_production(target_date, target_date)
        historical_data = self.query_engine.get_systems_production(start_date, target_date - timedelta(days=1))
        
        # Initialize result structure
        result = {
            "date": target_date.isoformat(),
            "systems": [],
            "summary": {
                "total_systems": len(current_data['sistemas']),
                "systems_with_deviation": 0,
                "comparison_period": {
                    "start": start_date.isoformat(),
                    "end": (target_date - timedelta(days=1)).isoformat()
                }
            }
        }
        
        # Process each system
        for system_id, system_data in current_data['sistemas'].items():
            try:
                # Get current day's production
                current_production = system_data['produccion']['total_energia_kwh']
                
                # Get historical production data
                if system_id in historical_data['sistemas']:
                    hist_system = historical_data['sistemas'][system_id]
                    daily_data = hist_system['produccion']['generacion_diaria']
                    
                    # Check if we have enough data for reliable analysis
                    if len(daily_data) >= min_days_required:
                        # Calculate statistics
                        daily_values = [day['energia_kwh'] for day in daily_data]
                        avg_production = sum(daily_values) / len(daily_values)
                        
                        # Calculate standard deviation
                        squared_diff_sum = sum((x - avg_production) ** 2 for x in daily_values)
                        std_dev = (squared_diff_sum / len(daily_values)) ** 0.5
                        
                        if std_dev > 0:  # Avoid division by zero
                            deviation = (current_production - avg_production) / std_dev
                            
                            # Only flag systems performing below average
                            if deviation < -std_dev_threshold:
                                percent_diff = ((current_production - avg_production) / avg_production) * 100
                                
                                result["systems"].append({
                                    "id": system_data['metadata']['id'],
                                    "name": system_data['metadata']['nombre'],
                                    "current_kwh": current_production,
                                    "avg_kwh": avg_production,
                                    "std_dev": std_dev,
                                    "deviation": deviation,  # Will be negative
                                    "percent_diff": percent_diff,  # Will be negative
                                    "days_analyzed": len(daily_values)
                                })
                                result["summary"]["systems_with_deviation"] += 1
                
            except Exception as e:
                # Skip systems with errors and continue with next
                continue
        
        return result 

    def check_production_deviation_inverters(self, check_date=None, min_days_required=7, std_dev_threshold=1, days_to_compare=30):
        """
        Analyzes inverter production deviations by comparing a specific date against historical data.
        Only flags inverters performing significantly below their historical average.
        Requires minimum number of days of historical data for reliable analysis.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
            min_days_required (int, optional): Minimum days of historical data required for analysis.
                                            Inverters with less data will be skipped. Defaults to 7.
            std_dev_threshold (float, optional): Number of standard deviations to consider significant.
                                              Lower values catch more deviations. Defaults to 1.
            days_to_compare (int, optional): Number of past days to use for comparison. Defaults to 30.
        
        Output structure:
        {
            "date": str,                  # Date checked in ISO format
            "inverters": [                # List of inverters performing below average
                {
                    "id": int,           # Inverter ID
                    "name": str,         # System name the inverter belongs to
                    "current_kwh": float, # Current day's production
                    "avg_kwh": float,     # Average daily production
                    "std_dev": float,     # Standard deviation
                    "deviation": float,   # Number of standard deviations from mean (negative)
                    "percent_diff": float, # Percentage difference from mean (negative)
                    "days_analyzed": int  # Number of days used in analysis
                },
                ...
            ],
            "summary": {
                "total_inverters": int,   # Total number of inverters checked
                "inverters_with_deviation": int,  # Number of inverters with significant deviation
                "comparison_period": {
                    "start": str,         # ISO date
                    "end": str           # ISO date
                }
            }
        }
        """
        # Get the dates to analyze
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        start_date = target_date - timedelta(days=days_to_compare)
        
        # Get production data for all inverters
        current_data = self.query_engine.get_inverters_production(target_date, target_date)
        historical_data = self.query_engine.get_inverters_production(start_date, target_date - timedelta(days=1))
        
        # Initialize result structure
        result = {
            "date": target_date.isoformat(),
            "inverters": [],
            "summary": {
                "total_inverters": len(current_data['inversores']),
                "inverters_with_deviation": 0,
                "comparison_period": {
                    "start": start_date.isoformat(),
                    "end": (target_date - timedelta(days=1)).isoformat()
                }
            }
        }
        
        # Process each inverter
        for inverter_id, inverter_data in current_data['inversores'].items():
            try:
                # Get current day's production
                current_production = inverter_data['produccion']['total_energia_kwh']
                
                # Get historical production data
                if inverter_id in historical_data['inversores']:
                    hist_inverter = historical_data['inversores'][inverter_id]
                    daily_data = hist_inverter['produccion']['generacion_diaria']
                    
                    # Check if we have enough data for reliable analysis
                    if len(daily_data) >= min_days_required:
                        # Calculate statistics
                        daily_values = [day['energia_kwh'] for day in daily_data]
                        avg_production = sum(daily_values) / len(daily_values)
                        
                        # Calculate standard deviation
                        squared_diff_sum = sum((x - avg_production) ** 2 for x in daily_values)
                        std_dev = (squared_diff_sum / len(daily_values)) ** 0.5
                        
                        if std_dev > 0:  # Avoid division by zero
                            deviation = (current_production - avg_production) / std_dev
                            
                            # Only flag inverters performing below average
                            if deviation < -std_dev_threshold:
                                percent_diff = ((current_production - avg_production) / avg_production) * 100
                                
                                result["inverters"].append({
                                    "id": inverter_data['metadata']['id'],
                                    "name": inverter_data['metadata']['proyecto']['nombre'],
                                    "current_kwh": current_production,
                                    "avg_kwh": avg_production,
                                    "std_dev": std_dev,
                                    "deviation": deviation,  # Will be negative
                                    "percent_diff": percent_diff,  # Will be negative
                                    "days_analyzed": len(daily_values)
                                })
                                result["summary"]["inverters_with_deviation"] += 1
                
            except Exception as e:
                # Skip inverters with errors and continue with next
                continue
        
        return result

    def check_production_deviation_granular(self, check_date=None, min_days_required=7, std_dev_threshold=1, days_to_compare=30):
        """
        Analyzes granular device production deviations by comparing a specific date against historical data.
        Only flags devices performing significantly below their historical average.
        Requires minimum number of days of historical data for reliable analysis.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
            min_days_required (int, optional): Minimum days of historical data required for analysis.
                                            Devices with less data will be skipped. Defaults to 7.
            std_dev_threshold (float, optional): Number of standard deviations to consider significant.
                                              Lower values catch more deviations. Defaults to 1.
            days_to_compare (int, optional): Number of past days to use for comparison. Defaults to 30.
        
        Output structure:
        {
            "date": str,                  # Date checked in ISO format
            "devices": [                  # List of devices performing below average
                {
                    "id": int,           # Device ID
                    "name": str,         # System name the device belongs to
                    "current_kwh": float, # Current day's production
                    "avg_kwh": float,     # Average daily production
                    "std_dev": float,     # Standard deviation
                    "deviation": float,   # Number of standard deviations from mean (negative)
                    "percent_diff": float, # Percentage difference from mean (negative)
                    "days_analyzed": int  # Number of days used in analysis
                },
                ...
            ],
            "summary": {
                "total_devices": int,     # Total number of devices checked
                "devices_with_deviation": int,  # Number of devices with significant deviation
                "comparison_period": {
                    "start": str,         # ISO date
                    "end": str           # ISO date
                }
            }
        }
        """
        # Get the dates to analyze
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        start_date = target_date - timedelta(days=days_to_compare)
        
        # Get production data for all granular devices
        current_data = self.query_engine.get_granular_production(target_date, target_date)
        historical_data = self.query_engine.get_granular_production(start_date, target_date - timedelta(days=1))
        
        # Initialize result structure
        result = {
            "date": target_date.isoformat(),
            "devices": [],
            "summary": {
                "total_devices": len(current_data['granular']),
                "devices_with_deviation": 0,
                "comparison_period": {
                    "start": start_date.isoformat(),
                    "end": (target_date - timedelta(days=1)).isoformat()
                }
            }
        }
        
        # Process each granular device
        for device_id, device_data in current_data['granular'].items():
            try:
                # Get current day's production
                current_production = device_data['produccion']['total_energia_kwh']
                
                # Get historical production data
                if device_id in historical_data['granular']:
                    hist_device = historical_data['granular'][device_id]
                    daily_data = hist_device['produccion']['generacion_diaria']
                    
                    # Check if we have enough data for reliable analysis
                    if len(daily_data) >= min_days_required:
                        # Calculate statistics
                        daily_values = [day['energia_kwh'] for day in daily_data]
                        avg_production = sum(daily_values) / len(daily_values)
                        
                        # Calculate standard deviation
                        squared_diff_sum = sum((x - avg_production) ** 2 for x in daily_values)
                        std_dev = (squared_diff_sum / len(daily_values)) ** 0.5
                        
                        if std_dev > 0:  # Avoid division by zero
                            deviation = (current_production - avg_production) / std_dev
                            
                            # Only flag devices performing below average
                            if deviation < -std_dev_threshold:
                                percent_diff = ((current_production - avg_production) / avg_production) * 100
                                
                                result["devices"].append({
                                    "id": device_data['metadata']['id'],
                                    "name": device_data['metadata']['proyecto']['nombre'],
                                    "current_kwh": current_production,
                                    "avg_kwh": avg_production,
                                    "std_dev": std_dev,
                                    "deviation": deviation,  # Will be negative
                                    "percent_diff": percent_diff,  # Will be negative
                                    "days_analyzed": len(daily_values)
                                })
                                result["summary"]["devices_with_deviation"] += 1
                
            except Exception as e:
                # Skip devices with errors and continue with next
                continue
        
        return result 