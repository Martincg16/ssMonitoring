"""
Query Engine for Solar Data Reports
Handles database queries for solar system analysis and reporting
"""

from django.db.models import Sum, Avg, Count
from solarData.models import Proyecto, GeneracionEnergiaDiaria
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
                    'energia_prometida_mes': float(sistema.energia_prometida_mes) if sistema.energia_prometida_mes else None
                },
                'produccion': {
                    'total_energia_kwh': float(total_energia_sistema),
                    'dias_con_datos': len(datos_diarios),
                    'promedio_diario_kwh': float(total_energia_sistema / len(datos_diarios)) if datos_diarios else 0,
                    'generacion_diaria': datos_diarios
                }
            }
            
            total_energia_general += total_energia_sistema
        
        # Update general summary
        result['resumen']['total_energia_kwh'] = float(total_energia_general)
        
        return result


# Convenience functions for common date ranges
def get_yesterday_production():
    """Get production data for yesterday only"""
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)
    
    query = SolarDataQuery()
    return query.get_systems_production(yesterday, yesterday)


def get_last_week_production():
    """Get production data for the last 7 days"""
    from datetime import date, timedelta
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=6)    # 7 days ago
    
    query = SolarDataQuery()
    return query.get_systems_production(start_date, end_date)
