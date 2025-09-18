"""
Analysis Engine for Solar Data Reports
Handles analysis of solar system data to detect anomalies and issues
"""

import logging
from datetime import datetime, date, timedelta
from django.db.models import Avg, StdDev, Count
from .query_engine import SolarDataQuery

# Initialize logger
logger = logging.getLogger('solarDataReports.analysis_engine')

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
        logger.info(f"Checking zero production systems for date: {target_date}")
        
        try:
            # Get production data for target date
            production_data = self.query_engine.get_systems_production(target_date, target_date)
            
            # Initialize result
            result = {
                "date": target_date.isoformat(),
                "systems": {
                    "zero": [],
                    "null": [],
                    "missing": []
                },
                "summary": {
                    "zero_count": 0,
                    "null_count": 0,
                    "missing_count": 0,
                    "total_systems_with_issues": 0
                }
            }
            
            # Check each system's production
            for system_id, system_data in production_data['sistemas'].items():
                logger.info(f"Analyzing system {system_data['metadata']['nombre']} (ID: {system_id})")
                
                try:
                    # Get target date's production data
                    daily_data = system_data['produccion']['generacion_diaria']
                    
                    # If no data for target date
                    if not daily_data:
                        logger.warning(f"No production data found for system {system_data['metadata']['nombre']} (ID: {system_id})")
                        result["systems"]["missing"].append({
                            "id": system_data['metadata']['id'],
                            "name": system_data['metadata']['nombre']
                        })
                        result["summary"]["missing_count"] += 1
                    # If data exists but is null
                    elif daily_data[0]['energia_kwh'] is None:
                        logger.warning(f"Null production value detected for system {system_data['metadata']['nombre']} (ID: {system_id})")
                        result["systems"]["null"].append({
                            "id": system_data['metadata']['id'],
                            "name": system_data['metadata']['nombre']
                        })
                        result["summary"]["null_count"] += 1
                    # If data exists but shows zero production
                    elif daily_data[0]['energia_kwh'] == 0:
                        logger.warning(f"Zero production detected for system {system_data['metadata']['nombre']} (ID: {system_id})")
                        result["systems"]["zero"].append({
                            "id": system_data['metadata']['id'],
                            "name": system_data['metadata']['nombre']
                        })
                        result["summary"]["zero_count"] += 1
                        
                except Exception as e:
                    logger.error(f"Error analyzing system {system_data['metadata']['nombre']} (ID: {system_id}): {str(e)}")
                    continue
            
            logger.info(f"Zero production check completed. Found {len(result['systems'])} systems with issues")
            return result
            
        except Exception as e:
            logger.error(f"Error in check_zero_production_system_single_day: {str(e)}")
            raise

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
        logger.info(f"Checking zero production inverters for date: {target_date}")
        
        try:
            # Get production data for target date
            production_data = self.query_engine.get_inverters_production(target_date, target_date)
            
            # Initialize result
            result = {
                "date": target_date.isoformat(),
                "inverters": {
                    "zero": [],
                    "null": [],
                    "missing": []
                },
                "summary": {
                    "zero_count": 0,
                    "null_count": 0,
                    "missing_count": 0,
                    "total_inverters_with_issues": 0
                }
            }
            
            # Check each inverter's production
            for inverter_id, inverter_data in production_data['inversores'].items():
                logger.info(f"Analyzing inverter ID: {inverter_id} from system {inverter_data['metadata']['proyecto']['nombre']}")
                
                try:
                    # Get target date's production data
                    daily_data = inverter_data['produccion']['generacion_diaria']
                    
                    # If no data for target date
                    if not daily_data:
                        logger.warning(f"No production data found for inverter {inverter_id} in system {inverter_data['metadata']['proyecto']['nombre']}")
                        result["inverters"]["missing"].append({
                            "id": inverter_data['metadata']['id'],
                            "name": inverter_data['metadata']['proyecto']['nombre']
                        })
                        result["summary"]["missing_count"] += 1
                    # If data exists but is null
                    elif daily_data[0]['energia_kwh'] is None:
                        logger.warning(f"Null production value detected for inverter {inverter_id} in system {inverter_data['metadata']['proyecto']['nombre']}")
                        result["inverters"]["null"].append({
                            "id": inverter_data['metadata']['id'],
                            "name": inverter_data['metadata']['proyecto']['nombre']
                        })
                        result["summary"]["null_count"] += 1
                    # If data exists but shows zero production
                    elif daily_data[0]['energia_kwh'] == 0:
                        logger.warning(f"Zero production detected for inverter {inverter_id} in system {inverter_data['metadata']['proyecto']['nombre']}")
                        result["inverters"]["zero"].append({
                            "id": inverter_data['metadata']['id'],
                            "name": inverter_data['metadata']['proyecto']['nombre']
                        })
                        result["summary"]["zero_count"] += 1
                        
                except Exception as e:
                    logger.error(f"Error analyzing inverter {inverter_id}: {str(e)}")
                    continue
            
            logger.info(f"Zero production check completed. Found {len(result['inverters'])} inverters with issues")
            return result
            
        except Exception as e:
            logger.error(f"Error in check_zero_production_inverter_single_day: {str(e)}")
            raise

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
        logger.info(f"Checking zero production granular devices for date: {target_date}")
        
        try:
            # Get production data for target date
            production_data = self.query_engine.get_granular_production(target_date, target_date)
            
            # Initialize result
            result = {
                "date": target_date.isoformat(),
                "devices": []
            }
            
            # Check each granular device's production
            for device_id, device_data in production_data['granular'].items():
                logger.info(f"Analyzing granular device ID: {device_id} from system {device_data['metadata']['proyecto']['nombre']}")
                
                try:
                    # Get target date's production data
                    daily_data = device_data['produccion']['generacion_diaria']
                    
                    # If no data for target date
                    if not daily_data:
                        logger.warning(f"No production data found for granular device {device_id} in system {device_data['metadata']['proyecto']['nombre']}")
                        result["devices"].append({
                            "id": device_data['metadata']['id'],
                            "name": device_data['metadata']['proyecto']['nombre'],
                            "type": "missing"
                        })
                    # If data exists but shows zero production
                    elif daily_data[0]['energia_kwh'] == 0:
                        logger.warning(f"Zero production detected for granular device {device_id} in system {device_data['metadata']['proyecto']['nombre']}")
                        result["devices"].append({
                            "id": device_data['metadata']['id'],
                            "name": device_data['metadata']['proyecto']['nombre'],
                            "type": "zero"
                        })
                        
                except Exception as e:
                    logger.error(f"Error analyzing granular device {device_id}: {str(e)}")
                    continue
            
            logger.info(f"Zero production check completed. Found {len(result['devices'])} granular devices with issues")
            return result
            
        except Exception as e:
            logger.error(f"Error in check_zero_production_granular_single_day: {str(e)}")
            raise

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
        
        logger.info(f"Analyzing system production deviations for date: {target_date}")
        logger.info(f"Using historical data from {start_date} to {target_date - timedelta(days=1)}")
        logger.info(f"Analysis parameters: min_days={min_days_required}, std_dev_threshold={std_dev_threshold}")
        
        try:
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
                logger.info(f"Analyzing deviations for system {system_data['metadata']['nombre']} (ID: {system_id})")
                
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
                                    
                                    logger.warning(
                                        f"Significant deviation detected for system {system_data['metadata']['nombre']} "
                                        f"(ID: {system_id}). Current: {current_production:.2f} kWh, "
                                        f"Avg: {avg_production:.2f} kWh, "
                                        f"Deviation: {deviation:.2f} std, "
                                        f"Percent diff: {percent_diff:.2f}%"
                                    )
                                    
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
                        else:
                            logger.debug(
                                f"Skipping system {system_data['metadata']['nombre']} (ID: {system_id}). "
                                f"Insufficient historical data: {len(daily_data)} days < {min_days_required} required"
                            )
                    
                except Exception as e:
                    logger.error(f"Error analyzing system {system_data['metadata']['nombre']} (ID: {system_id}): {str(e)}")
                    continue
            
            logger.info(
                f"Production deviation analysis completed. "
                f"Found {result['summary']['systems_with_deviation']} systems with significant deviations "
                f"out of {result['summary']['total_systems']} total systems"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in check_production_deviation_systems: {str(e)}")
            raise

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
        
        logger.info(f"Analyzing inverter production deviations for date: {target_date}")
        logger.info(f"Using historical data from {start_date} to {target_date - timedelta(days=1)}")
        logger.info(f"Analysis parameters: min_days={min_days_required}, std_dev_threshold={std_dev_threshold}")
        
        try:
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
                logger.info(f"Analyzing deviations for inverter {inverter_id} in system {inverter_data['metadata']['proyecto']['nombre']}")
                
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
                                    
                                    logger.warning(
                                        f"Significant deviation detected for inverter {inverter_id} "
                                        f"in system {inverter_data['metadata']['proyecto']['nombre']}. "
                                        f"Current: {current_production:.2f} kWh, "
                                        f"Avg: {avg_production:.2f} kWh, "
                                        f"Deviation: {deviation:.2f} std, "
                                        f"Percent diff: {percent_diff:.2f}%"
                                    )
                                    
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
                        else:
                            logger.debug(
                                f"Skipping inverter {inverter_id}. "
                                f"Insufficient historical data: {len(daily_data)} days < {min_days_required} required"
                            )
                    
                except Exception as e:
                    logger.error(f"Error analyzing inverter {inverter_id}: {str(e)}")
                    continue
            
            logger.info(
                f"Production deviation analysis completed. "
                f"Found {result['summary']['inverters_with_deviation']} inverters with significant deviations "
                f"out of {result['summary']['total_inverters']} total inverters"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in check_production_deviation_inverters: {str(e)}")
            raise

    def check_minimum_production_system_single_day(self, check_date=None):
        """
        Checks which systems are below their promised or minimum energy targets for a specific date.
        If no date is provided, checks yesterday's data.
        
        Args:
            check_date (date, optional): The date to check. Defaults to yesterday.
            
        Output structure:
        {
            "date": str,                  # ISO format date
            "systems": {
                "prometida": [            # List of systems below promised energy
                    {
                        "id": int,
                        "name": str,
                        "actual_kwh": float,
                        "promised_daily_kwh": float
                    },
                    ...
                ],
                "minima": [              # List of systems below minimum energy
                    {
                        "id": int,
                        "name": str,
                        "actual_kwh": float,
                        "minimum_daily_kwh": float
                    },
                    ...
                ]
            },
            "summary": {
                "total_systems_below_standards": int,
                "prometida_count": int,
                "minima_count": int,
                "both_standards_count": int
            }
        }
        """
        # Get the date to check
        target_date = check_date if check_date else date.today() - timedelta(days=1)
        logger.info(f"Checking minimum production systems for date: {target_date}")
        
        try:
            # Get production data for target date
            production_data = self.query_engine.get_systems_production(target_date, target_date)
            
            # Initialize result
            result = {
                "date": target_date.isoformat(),
                "systems": {
                    "prometida": [],
                    "minima": []
                },
                "summary": {
                    "total_systems_below_standards": 0,
                    "prometida_count": 0,
                    "minima_count": 0,
                    "both_standards_count": 0
                }
            }
            
            # Track systems failing both standards
            systems_below_both = set()
            
            # Check each system's production
            for system_id, system_data in production_data['sistemas'].items():
                logger.info(f"Analyzing system {system_data['metadata']['nombre']} (ID: {system_id})")
                
                try:
                    # Get target date's production data
                    daily_data = system_data['produccion']['generacion_diaria']
                    
                    # Skip if no data for target date
                    if not daily_data:
                        logger.debug(f"No production data found for system {system_data['metadata']['nombre']} (ID: {system_id})")
                        continue
                    
                    # Get actual production
                    actual_kwh = daily_data[0]['energia_kwh']
                    
                    # Get promised and minimum targets
                    promised_monthly = system_data['metadata'].get('energia_prometida_mes')
                    minimum_monthly = system_data['metadata'].get('energia_minima_mes')
                    
                    # Calculate daily targets (divide by 30)
                    try:
                        promised_daily = float(promised_monthly) / 30 if promised_monthly else None
                    except (ValueError, TypeError):
                        promised_daily = None
                        logger.warning(f"Invalid promised energy value for system {system_data['metadata']['nombre']} (ID: {system_id})")
                    
                    try:
                        minimum_daily = float(minimum_monthly) / 30 if minimum_monthly else None
                    except (ValueError, TypeError):
                        minimum_daily = None
                        logger.warning(f"Invalid minimum energy value for system {system_data['metadata']['nombre']} (ID: {system_id})")
                    
                    system_info = {
                        "id": system_data['metadata']['id'],
                        "name": system_data['metadata']['nombre'],
                        "actual_kwh": actual_kwh
                    }
                    
                    # Check against promised energy (treat null as failure)
                    if promised_daily is None or actual_kwh < promised_daily:
                        system_info_promised = system_info.copy()
                        system_info_promised["promised_daily_kwh"] = promised_daily if promised_daily is not None else 0
                        result["systems"]["prometida"].append(system_info_promised)
                        result["summary"]["prometida_count"] += 1
                        systems_below_both.add(system_id)
                        
                        if promised_daily is None:
                            logger.warning(
                                f"System {system_data['metadata']['nombre']} (ID: {system_id}) "
                                f"has no promised energy target defined"
                            )
                        else:
                            logger.warning(
                                f"System {system_data['metadata']['nombre']} (ID: {system_id}) "
                                f"below promised energy: {actual_kwh:.2f} kWh < {promised_daily:.2f} kWh"
                            )
                    
                    # Check against minimum energy (treat null as failure)
                    if minimum_daily is None or actual_kwh < minimum_daily:
                        system_info_minimum = system_info.copy()
                        system_info_minimum["minimum_daily_kwh"] = minimum_daily if minimum_daily is not None else 0
                        result["systems"]["minima"].append(system_info_minimum)
                        result["summary"]["minima_count"] += 1
                        
                        if system_id in systems_below_both:
                            result["summary"]["both_standards_count"] += 1
                        
                        if minimum_daily is None:
                            logger.warning(
                                f"System {system_data['metadata']['nombre']} (ID: {system_id}) "
                                f"has no minimum energy target defined"
                            )
                        else:
                            logger.warning(
                                f"System {system_data['metadata']['nombre']} (ID: {system_id}) "
                                f"below minimum energy: {actual_kwh:.2f} kWh < {minimum_daily:.2f} kWh"
                            )
                        
                except Exception as e:
                    logger.error(f"Error analyzing system {system_data['metadata']['nombre']} (ID: {system_id}): {str(e)}")
                    continue
            
            # Calculate total systems below standards
            result["summary"]["total_systems_below_standards"] = len(set(
                [item["id"] for item in result["systems"]["prometida"]] +
                [item["id"] for item in result["systems"]["minima"]]
            ))
            
            logger.info(
                f"Minimum production check completed. "
                f"Found {result['summary']['total_systems_below_standards']} systems below standards "
                f"({result['summary']['prometida_count']} below promised, "
                f"{result['summary']['minima_count']} below minimum, "
                f"{result['summary']['both_standards_count']} below both)"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in check_minimum_production_system_single_day: {str(e)}")
            raise

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
        
        logger.info(f"Analyzing granular device production deviations for date: {target_date}")
        logger.info(f"Using historical data from {start_date} to {target_date - timedelta(days=1)}")
        logger.info(f"Analysis parameters: min_days={min_days_required}, std_dev_threshold={std_dev_threshold}")
        
        try:
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
                logger.info(f"Analyzing deviations for granular device {device_id} in system {device_data['metadata']['proyecto']['nombre']}")
                
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
                                    
                                    logger.warning(
                                        f"Significant deviation detected for granular device {device_id} "
                                        f"in system {device_data['metadata']['proyecto']['nombre']}. "
                                        f"Current: {current_production:.2f} kWh, "
                                        f"Avg: {avg_production:.2f} kWh, "
                                        f"Deviation: {deviation:.2f} std, "
                                        f"Percent diff: {percent_diff:.2f}%"
                                    )
                                    
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
                        else:
                            logger.debug(
                                f"Skipping granular device {device_id}. "
                                f"Insufficient historical data: {len(daily_data)} days < {min_days_required} required"
                            )
                    
                except Exception as e:
                    logger.error(f"Error analyzing granular device {device_id}: {str(e)}")
                    continue
            
            logger.info(
                f"Production deviation analysis completed. "
                f"Found {result['summary']['devices_with_deviation']} devices with significant deviations "
                f"out of {result['summary']['total_devices']} total devices"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in check_production_deviation_granular: {str(e)}")
            raise 