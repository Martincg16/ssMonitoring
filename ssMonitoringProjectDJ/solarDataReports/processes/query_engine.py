"""
Query Engine for Solar Data Reports
Handles database queries for solar system analysis and reporting
"""

from django.db.models import Sum, Avg, Count
from solarData.models import Proyecto, GeneracionEnergiaDiaria, Inversor, GeneracionInversorDiaria, Granular, GeneracionGranularDiaria
from datetime import datetime, date


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
            
        Returns:
            dict: Structured data with system production information
        """
        
        # Get all solar systems (projects)
        sistemas = Proyecto.objects.all()
        
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
            
            # Add system data to result
            result['sistemas'][str(sistema.id)] = {
                'metadata': {
                    'id': sistema.id,
                    'nombre': sistema.dealname,
                    'ciudad': sistema.ciudad,
                    'departamento': sistema.departamento,
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
        
        # Update general summary
        result['resumen']['total_energia_kwh'] = float(total_energia_general)
        
        return result

    def get_inverters_production(self, start_date, end_date):
        """
        Get inverter production data for a date range
        
        Args:
            start_date (date): Start date for the query
            end_date (date): End date for the query (inclusive)
            
        Returns:
            dict: Structured data with inverter production information (flat structure)
        """
        
        # Get all inverters
        inversores = Inversor.objects.select_related('id_proyecto', 'id_proyecto__marca_inversor').all()
        
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
            
            # Add inverter data to result
            result['inversores'][str(inversor.id)] = {
                'metadata': {
                    'id': inversor.id,
                    'proyecto': {
                        'nombre': inversor.id_proyecto.dealname,
                        'ciudad': inversor.id_proyecto.ciudad,
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
        
        # Update general summary
        result['resumen']['total_energia_kwh'] = float(total_energia_general)
        
        return result

    def get_granular_production(self, start_date, end_date):
        """
        Get granular production data for a date range
        
        Args:
            start_date (date): Start date for the query
            end_date (date): End date for the query (inclusive)
            
        Returns:
            dict: Structured data with granular production information
        """
        
        # Get all granular data
        granular_data = Granular.objects.select_related('id_proyecto', 'id_proyecto__marca_inversor').all()
        
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
            
            # Add granular data to result
            result['granular'][str(granular_unit.id)] = {
                'metadata': {
                    'id': granular_unit.id,
                    'proyecto': {
                        'nombre': granular_unit.id_proyecto.dealname,
                        'ciudad': granular_unit.id_proyecto.ciudad
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
        
        # Update general summary
        result['resumen']['total_energia_kwh'] = float(total_energia_general)
        
        return result


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
