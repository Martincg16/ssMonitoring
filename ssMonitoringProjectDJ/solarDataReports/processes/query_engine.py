"""
Query Engine for Solar Data Reports
Handles database queries for solar system analysis and reporting
"""

import logging
from django.db.models import Sum, Avg, Count
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, date

# Initialize logger
logger = logging.getLogger('solarDataReports.query_engine')

class SolarDataQuery:
    """
    Main query engine for solar data reports
    Provides methods to extract solar system data for analysis
    """
    
    def get_systems_production(self, start_date, end_date):
        """
        Get solar system production data for a date range
        
        Args:
            start_date (date): Start date for the query
            end_date (date): End date for the query (inclusive)
            
        Output structure:
        {
            "sistemas": {
                "system_id": {                    # Key is the system ID as string
                    "metadata": {
                        "id": int,                # System ID
                        "nombre": str,            # System name
                        "ciudad": str,            # City name or null
                        "departamento": str,      # Department name or null
                        "marca_inversor": str,    # Inverter brand or null
                        "capacidad_instalada_dc": float,  # DC capacity or null
                        "capacidad_instalada_ac": float,  # AC capacity or null
                        "fecha_entrada_operacion": str,   # ISO date or null
                        "energia_prometida_mes": float,   # Monthly promised energy or null
                        "energia_minima_mes": float,      # Minimum monthly energy or null
                        "restriccion_de_autoconsumo": bool
                    },
                    "produccion": {
                        "total_energia_kwh": float,      # Total energy in date range
                        "dias_con_datos": int,           # Number of days with data
                        "generacion_diaria": [           # Daily generation list
                            {
                                "fecha": str,            # ISO date
                                "energia_kwh": float     # Daily energy
                            },
                            ...
                        ]
                    }
                },
                ...
            },
            "resumen": {
                "total_sistemas": int,            # Total number of systems
                "rango_fechas": {
                    "inicio": str,                # ISO date
                    "fin": str                    # ISO date
                },
                "total_energia_kwh": float        # Total energy all systems
            }
        }
        """
        logger.info(f"Querying systems production from {start_date} to {end_date}")
        
        try:
            # Get all solar systems (projects)
            sistemas = Proyecto.objects.all()
            logger.info(f"Found {sistemas.count()} systems to analyze")
            
            result = {
                'sistemas': {},
                'resumen': {
                    'total_sistemas': sistemas.count(),
                    'rango_fechas': {
                        'inicio': start_date.isoformat(),
                        'fin': end_date.isoformat()
                    },
                    'total_energia_kwh': 0
                }
            }
            
            total_energia_general = 0
            
            # Loop through each system to get its production data
            for sistema in sistemas:
                logger.debug(f"Processing system {sistema.dealname} (ID: {sistema.id})")
                
                try:
                    # Get daily generation data for this system in the date range
                    generacion_diaria = GeneracionEnergiaDiaria.objects.filter(
                        id_proyecto=sistema,
                        fecha_generacion_dia__gte=start_date,
                        fecha_generacion_dia__lte=end_date
                    ).order_by('fecha_generacion_dia')
                    
                    # Calculate system totals
                    total_energia_sistema = generacion_diaria.aggregate(
                        total=Sum('energia_generada_dia')
                    )['total'] or 0
                    
                    # Build daily data list
                    datos_diarios = []
                    for gen in generacion_diaria:
                        datos_diarios.append({
                            'fecha': gen.fecha_generacion_dia.isoformat(),
                            'energia_kwh': float(gen.energia_generada_dia) if gen.energia_generada_dia else 0
                        })
                    
                    logger.debug(f"System {sistema.dealname} has {len(datos_diarios)} days of data, total energy: {total_energia_sistema} kWh")
                    
                    # Add system data to result
                    result['sistemas'][str(sistema.id)] = {
                        'metadata': {
                            'id': sistema.id,
                            'nombre': sistema.dealname,
                            'ciudad': sistema.id_ciudad.nombre_ciudad if sistema.id_ciudad else None,
                            'departamento': sistema.id_ciudad.id_departamento.nombre_departamento if sistema.id_ciudad else None,
                            'marca_inversor': sistema.marca_inversor.marca if sistema.marca_inversor else None,
                            'capacidad_instalada_dc': float(sistema.capacidad_instalada_dc) if sistema.capacidad_instalada_dc else None,
                            'capacidad_instalada_ac': float(sistema.capacidad_instalada_ac) if sistema.capacidad_instalada_ac else None,
                            'fecha_entrada_operacion': sistema.fecha_entrada_en_operacion.isoformat() if sistema.fecha_entrada_en_operacion else None,
                            'energia_prometida_mes': float(sistema.energia_prometida_mes) if sistema.energia_prometida_mes else None,
                            'energia_minima_mes': float(sistema.energia_minima_mes) if sistema.energia_minima_mes else None,
                            'restriccion_de_autoconsumo': sistema.restriccion_de_autoconsumo
                        },
                        'produccion': {
                            'total_energia_kwh': float(total_energia_sistema),
                            'dias_con_datos': len(datos_diarios),
                            'generacion_diaria': datos_diarios
                        }
                    }
                    
                    total_energia_general += total_energia_sistema
                    
                except Exception as e:
                    logger.error(f"Error processing system {sistema.dealname} (ID: {sistema.id}): {str(e)}")
                    continue
            
            # Update general summary
            result['resumen']['total_energia_kwh'] = float(total_energia_general)
            
            logger.info(f"Query completed successfully. Total energy across all systems: {total_energia_general} kWh")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_systems_production: {str(e)}")
            raise

    def get_inverters_production(self, start_date, end_date):
        """
        Get inverter production data for a date range
        
        Args:
            start_date (date): Start date for the query
            end_date (date): End date for the query (inclusive)
            
        Output structure:
        {
            "inversores": {
                "inverter_id": {                  # Key is the inverter ID as string
                    "metadata": {
                        "id": int,                # Inverter ID
                        "proyecto": {
                            "nombre": str,        # System name
                            "ciudad": str,        # City name or null
                            "marca_inversor": str # Inverter brand or null
                        }
                    },
                    "produccion": {
                        "total_energia_kwh": float,     # Total energy in date range
                        "dias_con_datos": int,          # Number of days with data
                        "generacion_diaria": [          # Daily generation list
                            {
                                "fecha": str,           # ISO date
                                "energia_kwh": float    # Daily energy
                            },
                            ...
                        ]
                    }
                },
                ...
            },
            "resumen": {
                "total_inversores": int,          # Total number of inverters
                "rango_fechas": {
                    "inicio": str,                # ISO date
                    "fin": str                    # ISO date
                },
                "total_energia_kwh": float        # Total energy all inverters
            }
        }
        """
        logger.info(f"Querying inverters production from {start_date} to {end_date}")
        
        try:
            # Get all inverters
            inversores = Inversor.objects.select_related('id_proyecto', 'id_proyecto__marca_inversor').all()
            logger.info(f"Found {inversores.count()} inverters to analyze")
            
            result = {
                'inversores': {},
                'resumen': {
                    'total_inversores': inversores.count(),
                    'rango_fechas': {
                        'inicio': start_date.isoformat(),
                        'fin': end_date.isoformat()
                    },
                    'total_energia_kwh': 0
                }
            }
            
            total_energia_general = 0
            
            # Loop through each inverter to get its production data
            for inversor in inversores:
                logger.debug(f"Processing inverter ID: {inversor.id} from system {inversor.id_proyecto.dealname}")
                
                try:
                    # Get daily generation data for this inverter in the date range
                    generacion_diaria = GeneracionInversorDiaria.objects.filter(
                        id_inversor=inversor,
                        fecha_generacion_inversor_dia__gte=start_date,
                        fecha_generacion_inversor_dia__lte=end_date
                    ).order_by('fecha_generacion_inversor_dia')
                    
                    # Calculate inverter totals
                    total_energia_inversor = generacion_diaria.aggregate(
                        total=Sum('energia_generada_inversor_dia')
                    )['total'] or 0
                    
                    # Build daily data list
                    datos_diarios = []
                    for gen in generacion_diaria:
                        datos_diarios.append({
                            'fecha': gen.fecha_generacion_inversor_dia.isoformat(),
                            'energia_kwh': float(gen.energia_generada_inversor_dia) if gen.energia_generada_inversor_dia else 0
                        })
                    
                    logger.debug(f"Inverter {inversor.id} has {len(datos_diarios)} days of data, total energy: {total_energia_inversor} kWh")
                    
                    # Add inverter data to result
                    result['inversores'][str(inversor.id)] = {
                        'metadata': {
                            'id': inversor.id,
                            'proyecto': {
                                'nombre': inversor.id_proyecto.dealname,
                                'ciudad': inversor.id_proyecto.id_ciudad.nombre_ciudad if inversor.id_proyecto.id_ciudad else None,
                                'marca_inversor': inversor.id_proyecto.marca_inversor.marca if inversor.id_proyecto.marca_inversor else None
                            }
                        },
                        'produccion': {
                            'total_energia_kwh': float(total_energia_inversor),
                            'dias_con_datos': len(datos_diarios),
                            'generacion_diaria': datos_diarios
                        }
                    }
                    
                    total_energia_general += total_energia_inversor
                    
                except Exception as e:
                    logger.error(f"Error processing inverter ID {inversor.id}: {str(e)}")
                    continue
            
            # Update general summary
            result['resumen']['total_energia_kwh'] = float(total_energia_general)
            
            logger.info(f"Query completed successfully. Total energy across all inverters: {total_energia_general} kWh")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_inverters_production: {str(e)}")
            raise

    def get_granular_production(self, start_date, end_date):
        """
        Get granular production data for a date range
        
        Args:
            start_date (date): Start date for the query
            end_date (date): End date for the query (inclusive)
            
        Output structure:
        {
            "granular": {
                "granular_id": {                  # Key is the granular ID as string
                    "metadata": {
                        "id": int,                # Granular ID
                        "proyecto": {
                            "nombre": str,        # System name
                            "ciudad": str,        # City name or null
                            "marca_inversor": str # Inverter brand or null
                        }
                    },
                    "produccion": {
                        "total_energia_kwh": float,     # Total energy in date range
                        "dias_con_datos": int,          # Number of days with data
                        "generacion_diaria": [          # Daily generation list
                            {
                                "fecha": str,           # ISO date
                                "energia_kwh": float    # Daily energy
                            },
                            ...
                        ]
                    }
                },
                ...
            },
            "resumen": {
                "total_granular": int,            # Total number of granular devices
                "rango_fechas": {
                    "inicio": str,                # ISO date
                    "fin": str                    # ISO date
                },
                "total_energia_kwh": float        # Total energy all granular
            }
        }
        """
        logger.info(f"Querying granular production from {start_date} to {end_date}")
        
        try:
            # Get all granular data
            granular_data = Granular.objects.select_related('id_proyecto', 'id_proyecto__marca_inversor').all()
            logger.info(f"Found {granular_data.count()} granular devices to analyze")
            
            result = {
                'granular': {},
                'resumen': {
                    'total_granular': granular_data.count(),
                    'rango_fechas': {
                        'inicio': start_date.isoformat(),
                        'fin': end_date.isoformat()
                    },
                    'total_energia_kwh': 0
                }
            }
            
            total_energia_general = 0
            
            # Loop through each granular unit to get its production data
            for granular_unit in granular_data:
                logger.debug(f"Processing granular device ID: {granular_unit.id} from system {granular_unit.id_proyecto.dealname}")
                
                try:
                    # Get daily generation data for this granular unit in the date range
                    generacion_diaria = GeneracionGranularDiaria.objects.filter(
                        id_granular=granular_unit,
                        fecha_generacion_granular_dia__gte=start_date,
                        fecha_generacion_granular_dia__lte=end_date
                    ).order_by('fecha_generacion_granular_dia')
                    
                    # Calculate granular totals
                    total_energia_granular = generacion_diaria.aggregate(
                        total=Sum('energia_generada_granular_dia')
                    )['total'] or 0
                    
                    # Build daily data list
                    datos_diarios = []
                    for gen in generacion_diaria:
                        datos_diarios.append({
                            'fecha': gen.fecha_generacion_granular_dia.isoformat(),
                            'energia_kwh': float(gen.energia_generada_granular_dia) if gen.energia_generada_granular_dia else 0
                        })
                    
                    logger.debug(f"Granular device {granular_unit.id} has {len(datos_diarios)} days of data, total energy: {total_energia_granular} kWh")
                    
                    # Add granular data to result
                    result['granular'][str(granular_unit.id)] = {
                        'metadata': {
                            'id': granular_unit.id,
                            'proyecto': {
                                'nombre': granular_unit.id_proyecto.dealname,
                                'ciudad': granular_unit.id_proyecto.id_ciudad.nombre_ciudad if granular_unit.id_proyecto.id_ciudad else None
                            },
                            'inversor': {
                                'id': granular_unit.id_inversor.id,
                                'marca_inversor': granular_unit.id_proyecto.marca_inversor.marca if granular_unit.id_proyecto.marca_inversor else None
                            }
                        },
                        'produccion': {
                            'total_energia_kwh': float(total_energia_granular),
                            'dias_con_datos': len(datos_diarios),
                            'generacion_diaria': datos_diarios
                        }
                    }
                    
                    total_energia_general += total_energia_granular
                    
                except Exception as e:
                    logger.error(f"Error processing granular device ID {granular_unit.id}: {str(e)}")
                    continue
            
            # Update general summary
            result['resumen']['total_energia_kwh'] = float(total_energia_general)
            
            logger.info(f"Query completed successfully. Total energy across all granular devices: {total_energia_general} kWh")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_granular_production: {str(e)}")
            raise


# Convenience function for flexible date ranges
def get_last_n_days_production(n_days):
    """
    Get production data for the last n days
    
    Args:
        n_days (int): Number of days to retrieve (1 = yesterday only, 7 = last week, etc.)
        
    Returns:
        dict: Structured data with system production information
    """
    from datetime import date, timedelta
    
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=n_days - 1)  # n days ago
    
    query = SolarDataQuery()
    return query.get_systems_production(start_date, end_date)

def get_inverters_last_n_days_production(n_days):
    """
    Get inverter production data for the last n days
    
    Args:
        n_days (int): Number of days to retrieve (1 = yesterday only, 7 = last week, etc.)
        
    Returns:
        dict: Structured data with inverter production information (flat structure)
    """
    from datetime import date, timedelta
    
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=n_days - 1)  # n days ago
    
    query = SolarDataQuery()
    return query.get_inverters_production(start_date, end_date)

def get_granular_last_n_days_production(n_days):
    """
    Get granular production data for the last n days
    
    Args:
        n_days (int): Number of days to retrieve (1 = yesterday only, 7 = last week, etc.)
        
    Returns:
        dict: Structured data with granular production information (MPPT/string level)
    """
    from datetime import date, timedelta
    
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=n_days - 1)  # n days ago
    
    query = SolarDataQuery()
    return query.get_granular_production(start_date, end_date)
