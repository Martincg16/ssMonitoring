"""
Generate basic solar production report (PDF only, no email)
"""
import logging
import os
import shutil
from datetime import date
from django.core.management.base import BaseCommand
from solarDataReports.processes.analysis_engine import SolarDataAnalysis
from solarDataReports.processes.report_engine import SolarDataReporter
from solarDataReports.processes.pdf_generator_engine import SolarDataPDFGenerator

logger = logging.getLogger('solarData.management_commands')

class Command(BaseCommand):
    help = 'Generate basic solar production report (PDF only, no email)'

    def handle(self, *args, **options):
        try:
            self.stdout.write("Starting basic report generation...")
            
            # Initialize engines
            analysis = SolarDataAnalysis()
            reporter = SolarDataReporter()
            pdf_gen = SolarDataPDFGenerator()
            
            # Run all 6 analyses (defaults to yesterday)
            self.stdout.write("Running analyses...")
            results = {
                'no_target': analysis.check_systems_no_target(),
                'zero_systems': analysis.check_systems_zero_production_single_day(),
                'null_missing': analysis.check_systems_null_or_missing_single_day(),
                'under_target_15d': analysis.check_systems_under_target_15d(),
                'inverters_conditional': analysis.check_inverters_zero_conditional_single_day(),
                'granular_conditional': analysis.check_granular_zero_conditional_single_day()
            }
            
            # Get date for summary and filename
            report_date = results['zero_systems']['date']
            today = date.today()
            
            # Create summary header
            summary = f"""
{'='*60}
BASIC SOLAR PRODUCTION REPORT
{'='*60}
Generated on: {today.strftime('%Y-%m-%d')}
Analysis Date: {report_date}

SUMMARY OF ISSUES:
• Systems with no target defined: {results['no_target']['summary']['total_count']}
• Systems with 0 production: {results['zero_systems']['summary']['total_count']}
• Systems with null/missing data: {results['null_missing']['summary']['total_count']}
• Systems under 15-day target: {results['under_target_15d']['summary']['total_count']}
• Inverters with 0 (system produced): {results['inverters_conditional']['summary']['total_count']}
• Granular with 0 (inverter produced): {results['granular_conditional']['summary']['total_count']}

{'='*60}
"""
            
            # Translate each analysis result to text
            self.stdout.write("Generating report text...")
            reports = [
                summary,
                reporter.translate_systems_no_target(results['no_target']),
                reporter.translate_systems_zero_production(results['zero_systems']),
                reporter.translate_systems_null_or_missing(results['null_missing']),
                reporter.translate_systems_under_target_15d(results['under_target_15d']),
                reporter.translate_inverters_zero_conditional(results['inverters_conditional']),
                reporter.translate_granular_zero_conditional(results['granular_conditional'])
            ]
            
            # Generate PDF
            self.stdout.write("Creating PDF...")
            pdf_path = pdf_gen.simple_report(
                reports,
                title="Basic Solar Production Report",
                date=report_date
            )
            
            if not pdf_path:
                raise Exception("PDF generation failed")
            
            # Move PDF to solarDataReports folder
            self.stdout.write("Moving PDF to solarDataReports folder...")
            
            # Get solarDataReports directory path
            current_dir = os.path.dirname(os.path.abspath(__file__))  # commands/
            management_dir = os.path.dirname(current_dir)  # management/
            solarData_dir = os.path.dirname(management_dir)  # solarData/
            project_dir = os.path.dirname(solarData_dir)  # ssMonitoringProjectDJ/
            reports_dir = os.path.join(project_dir, 'solarDataReports')
            
            # Create filename
            filename = f"basic_report_{report_date}.pdf"
            target_path = os.path.join(reports_dir, filename)
            
            # Move file
            shutil.move(pdf_path, target_path)
            
            # Success message
            self.stdout.write(self.style.SUCCESS(f'\nBasic report generated successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Location: {target_path}'))
            self.stdout.write(f"\nSummary:")
            self.stdout.write(f"  - Systems with no target: {results['no_target']['summary']['total_count']}")
            self.stdout.write(f"  - Systems with 0: {results['zero_systems']['summary']['total_count']}")
            self.stdout.write(f"  - Systems with null/missing: {results['null_missing']['summary']['total_count']}")
            self.stdout.write(f"  - Systems under 15-day target: {results['under_target_15d']['summary']['total_count']}")
            self.stdout.write(f"  - Inverters flagged: {results['inverters_conditional']['summary']['total_count']}")
            self.stdout.write(f"  - Granular flagged: {results['granular_conditional']['summary']['total_count']}")
                
        except Exception as e:
            logger.error(f"Failed to generate basic report: {str(e)}")
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))
            raise
