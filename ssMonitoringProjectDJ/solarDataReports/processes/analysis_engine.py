"""
Analysis Engine for Solar Data Reports
Handles analysis of solar system data to detect anomalies and issues
"""

from datetime import datetime, date, timedelta
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