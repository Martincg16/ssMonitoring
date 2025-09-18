"""
Report Engine for Solar Data Reports
Handles translation of analysis results into human-readable text format
"""

import logging
from datetime import datetime

# Initialize logger
logger = logging.getLogger('solarDataReports.report_engine')

class SolarDataReporter:
    """
    Handles translation of analysis engine outputs into human-readable reports
    """
    
    def __init__(self):
        pass
    
    def translate_zero_production_results(self, result):
        """
        Converts zero production analysis to readable text
        
        Args:
            result (dict): Output from check_zero_production_*_single_day functions
            
        Returns:
            str: Human-readable text report
        """
        logger.debug(f"Translating zero production results for date: {result.get('date', 'unknown')}")
        
        try:
            report_lines = []
            date_str = result.get('date', 'Unknown Date')
            
            # Header
            report_lines.append("=" * 60)
            report_lines.append("ZERO PRODUCTION ANALYSIS REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Analysis Date: {date_str}")
            report_lines.append("")
            
            # Determine the type of analysis (systems, inverters, or devices)
            if 'systems' in result:
                entity_type = "Systems"
                entities = result['systems']
                summary_key = 'total_systems_with_issues'
            elif 'inverters' in result:
                entity_type = "Inverters"
                entities = result['inverters']
                summary_key = 'total_inverters_with_issues'
            elif 'devices' in result:
                entity_type = "Granular Devices"
                entities = result['devices']
                summary_key = 'total_devices_with_issues'
            else:
                return "Error: Unknown result format for zero production analysis"
            
            # Summary section
            summary = result.get('summary', {})
            total_issues = summary.get(summary_key, 0)
            zero_count = summary.get('zero_count', 0)
            null_count = summary.get('null_count', 0)
            missing_count = summary.get('missing_count', 0)
            
            report_lines.append("EXECUTIVE SUMMARY:")
            report_lines.append(f"- Total {entity_type.lower()} with production issues: {total_issues}")
            if zero_count > 0:
                report_lines.append(f"- {entity_type} with zero production: {zero_count}")
                for item in entities.get('zero', []):
                    report_lines.append(f"  • {item['name']}")
            if null_count > 0:
                report_lines.append(f"- {entity_type} with null production values: {null_count}")
                for item in entities.get('null', []):
                    report_lines.append(f"  • {item['name']}")
            if missing_count > 0:
                report_lines.append(f"- {entity_type} with missing production data: {missing_count}")
                for item in entities.get('missing', []):
                    report_lines.append(f"  • {item['name']}")
            report_lines.append("")
            
            # Detailed findings
            if total_issues > 0:
                report_lines.append("DETAILED FINDINGS:")
                report_lines.append("")
                
                # Zero production section
                if entities.get('zero'):
                    report_lines.append(f"{entity_type} with ZERO Production:")
                    report_lines.append("-" * 40)
                    for item in entities['zero']:
                        report_lines.append(f"• {item['name']} (ID: {item['id']})")
                    report_lines.append("")
                
                # Null production section
                if entities.get('null'):
                    report_lines.append(f"{entity_type} with NULL Production Values:")
                    report_lines.append("-" * 40)
                    for item in entities['null']:
                        report_lines.append(f"• {item['name']} (ID: {item['id']})")
                    report_lines.append("")
                
                # Missing production section
                if entities.get('missing'):
                    report_lines.append(f"{entity_type} with MISSING Production Data:")
                    report_lines.append("-" * 40)
                    for item in entities['missing']:
                        report_lines.append(f"• {item['name']} (ID: {item['id']})")
                    report_lines.append("")
            else:
                report_lines.append(f"All {entity_type.lower()} reported production data for {date_str}")
                report_lines.append("")
            
            # Recommendations
            if total_issues > 0:
                report_lines.append("RECOMMENDED ACTIONS:")
                report_lines.append("-" * 20)
                if zero_count > 0:
                    report_lines.append("• Investigate systems with zero production for equipment issues")
                if null_count > 0:
                    report_lines.append("• Check data collection systems for null value sources")
                if missing_count > 0:
                    report_lines.append("• Verify communication links for systems with missing data")
                report_lines.append("")
            
            logger.info(f"Successfully translated zero production results: {total_issues} issues found")
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error translating zero production results: {str(e)}")
            return f"Error generating zero production report: {str(e)}"
    
    def translate_minimum_production_results(self, result):
        """
        Converts quality standards analysis to readable text
        
        Args:
            result (dict): Output from check_minimum_production_*_single_day functions
            
        Returns:
            str: Human-readable text report
        """
        logger.debug(f"Translating minimum production results for date: {result.get('date', 'unknown')}")
        
        try:
            report_lines = []
            date_str = result.get('date', 'Unknown Date')
            
            # Header
            report_lines.append("=" * 60)
            report_lines.append("QUALITY STANDARDS COMPLIANCE REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Analysis Date: {date_str}")
            report_lines.append("")
            
            # Determine the type of analysis
            if 'systems' in result:
                entity_type = "Systems"
                entities = result['systems']
                summary_key = 'total_systems_below_standards'
            elif 'inverters' in result:
                entity_type = "Inverters"
                entities = result['inverters']
                summary_key = 'total_inverters_below_standards'
            elif 'devices' in result:
                entity_type = "Granular Devices"
                entities = result['devices']
                summary_key = 'total_devices_below_standards'
            else:
                return "Error: Unknown result format for minimum production analysis"
            
            # Summary section
            summary = result.get('summary', {})
            total_below = summary.get(summary_key, 0)
            prometida_count = summary.get('prometida_count', 0)
            minima_count = summary.get('minima_count', 0)
            both_count = summary.get('both_standards_count', 0)
            
            report_lines.append("EXECUTIVE SUMMARY:")
            report_lines.append(f"- Total {entity_type.lower()} below quality standards: {total_below}")
            if prometida_count > 0:
                report_lines.append(f"- {entity_type} below promised energy target: {prometida_count}")
                for item in entities.get('prometida', []):
                    report_lines.append(f"  • {item['name']} (Actual: {item['actual_kwh']:.2f} kWh vs Target: {item['promised_daily_kwh']:.2f} kWh)")
            if minima_count > 0:
                report_lines.append(f"- {entity_type} below minimum energy requirement: {minima_count}")
                for item in entities.get('minima', []):
                    report_lines.append(f"  • {item['name']} (Actual: {item['actual_kwh']:.2f} kWh vs Minimum: {item['minimum_daily_kwh']:.2f} kWh)")
            if both_count > 0:
                report_lines.append(f"- {entity_type} below both standards: {both_count}")
                both_items = [item for item in entities.get('prometida', []) if any(m['id'] == item['id'] for m in entities.get('minima', []))]
                for item in both_items:
                    report_lines.append(f"  • {item['name']}")
            report_lines.append("")
            
            # Detailed findings
            if total_below > 0:
                report_lines.append("DETAILED FINDINGS:")
                report_lines.append("")
                
                # Below promised standard section
                if entities.get('prometida'):
                    report_lines.append(f"{entity_type} Below PROMISED Energy Standard:")
                    report_lines.append("-" * 50)
                    for item in entities['prometida']:
                        actual = item['actual_kwh']
                        target = item['promised_daily_kwh']
                        report_lines.append(f"• {item['name']} (ID: {item['id']})")
                        report_lines.append(f"  Actual: {actual:.2f} kWh | Target: {target:.2f} kWh")
                    report_lines.append("")
                
                # Below minimum standard section
                if entities.get('minima'):
                    report_lines.append(f"{entity_type} Below MINIMUM Energy Requirement:")
                    report_lines.append("-" * 50)
                    for item in entities['minima']:
                        actual = item['actual_kwh']
                        target = item['minimum_daily_kwh']
                        report_lines.append(f"• {item['name']} (ID: {item['id']})")
                        report_lines.append(f"  Actual: {actual:.2f} kWh | Minimum: {target:.2f} kWh")
                    report_lines.append("")
            else:
                report_lines.append(f"All {entity_type.lower()} met quality standards for {date_str}")
                report_lines.append("")
            
            # Recommendations
            if total_below > 0:
                report_lines.append("RECOMMENDED ACTIONS:")
                report_lines.append("-" * 20)
                if prometida_count > 0:
                    report_lines.append("• Review performance of systems below promised targets")
                    report_lines.append("• Consider maintenance or optimization for underperforming systems")
                if minima_count > 0:
                    report_lines.append("• URGENT: Investigate systems below minimum requirements")
                    report_lines.append("• These systems may have critical issues requiring immediate attention")
                if both_count > 0:
                    report_lines.append("• Priority systems failing both standards need immediate intervention")
                report_lines.append("")
            
            logger.info(f"Successfully translated minimum production results: {total_below} systems below standards")
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error translating minimum production results: {str(e)}")
            return f"Error generating quality standards report: {str(e)}"
    
    def translate_deviation_analysis_results(self, result):
        """
        Converts deviation analysis to readable text
        
        Args:
            result (dict): Output from check_production_deviation_* functions
            
        Returns:
            str: Human-readable text report
        """
        logger.debug(f"Translating deviation analysis results for date: {result.get('date', 'unknown')}")
        
        try:
            report_lines = []
            date_str = result.get('date', 'Unknown Date')
            
            # Header
            report_lines.append("=" * 60)
            report_lines.append("PRODUCTION DEVIATION ANALYSIS REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Analysis Date: {date_str}")
            report_lines.append("")
            
            # Determine the type of analysis
            if 'systems' in result:
                entity_type = "Systems"
                entities = result['systems']
            elif 'inverters' in result:
                entity_type = "Inverters"
                entities = result['inverters']
            elif 'devices' in result:
                entity_type = "Granular Devices"
                entities = result['devices']
            else:
                return "Error: Unknown result format for deviation analysis"
            
            # Summary section
            summary = result.get('summary', {})
            total_deviations = summary.get('systems_with_deviation', 0) if 'systems' in result else \
                              summary.get('inverters_with_deviation', 0) if 'inverters' in result else \
                              summary.get('devices_with_deviation', 0)
            days_analyzed = summary.get('days_analyzed', 'unknown')
            threshold = summary.get('std_dev_threshold', 'unknown')
            
            report_lines.append("EXECUTIVE SUMMARY:")
            report_lines.append(f"- {entity_type} with significant production deviations: {total_deviations}")
            if total_deviations > 0:
                for item in entities:
                    name = item.get('name', 'Unknown')
                    current_prod = item.get('current_kwh', 0)
                    avg_prod = item.get('avg_kwh', 0)
                    percent_diff = item.get('percent_diff', 0)
                    report_lines.append(f"  • {name} ({percent_diff:.1f}% below average)")
                    report_lines.append(f"    Current: {current_prod:.2f} kWh vs Average: {avg_prod:.2f} kWh")
            report_lines.append(f"- Analysis period: {days_analyzed} days")
            report_lines.append(f"- Deviation threshold: {threshold} standard deviations below average")
            report_lines.append("")
            
            # Detailed findings
            if total_deviations > 0:
                report_lines.append("DETAILED FINDINGS:")
                report_lines.append(f"{entity_type} Performing Below Historical Average:")
                report_lines.append("-" * 60)
                
                for item in entities:
                    name = item.get('name', 'Unknown')
                    entity_id = item.get('id', 'Unknown')
                    current_prod = item.get('current_kwh', 0)
                    avg_prod = item.get('avg_kwh', 0)
                    deviation = item.get('deviation', 0)
                    percent_diff = item.get('percent_diff', 0)
                    
                    report_lines.append(f"• {name} (ID: {entity_id})")
                    report_lines.append(f"  Current Production: {current_prod:.2f} kWh")
                    report_lines.append(f"  Historical Average: {avg_prod:.2f} kWh")
                    report_lines.append(f"  Deviation Score: {deviation:.2f} std devs below average")
                    report_lines.append(f"  Performance Difference: {percent_diff:.1f}% below average")
                    report_lines.append("")
            else:
                report_lines.append(f"No {entity_type.lower()} showed significant deviations from historical performance on {date_str}")
                report_lines.append("")
            
            # Recommendations
            if total_deviations > 0:
                report_lines.append("RECOMMENDED ACTIONS:")
                report_lines.append("-" * 20)
                report_lines.append("• Investigate underperforming systems for potential issues:")
                report_lines.append("  - Equipment malfunctions or degradation")
                report_lines.append("  - Shading or environmental factors")
                report_lines.append("  - Maintenance requirements")
                report_lines.append("• Compare with weather data for the analysis date")
                report_lines.append("• Consider trending analysis for persistent underperformers")
                report_lines.append("")
            
            logger.info(f"Successfully translated deviation analysis results: {total_deviations} deviations found")
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error translating deviation analysis results: {str(e)}")
            return f"Error generating deviation analysis report: {str(e)}"
