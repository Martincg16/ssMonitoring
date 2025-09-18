"""
Generate and email daily solar production report for yesterday
"""
import logging
from datetime import date
from django.core.management.base import BaseCommand
from solarDataReports.processes.analysis_engine import SolarDataAnalysis
from solarDataReports.processes.report_engine import SolarDataReporter
from solarDataReports.processes.pdf_generator_engine import SolarDataPDFGenerator
from solarDataReports.processes.email_sender_engine import SolarDataEmailSender

logger = logging.getLogger('solarData.management_commands')

class Command(BaseCommand):
    help = 'Generate and email daily solar production report for yesterday'

    def handle(self, *args, **options):
        try:
            # Initialize engines
            analysis = SolarDataAnalysis()
            reporter = SolarDataReporter()
            pdf_gen = SolarDataPDFGenerator()
            email = SolarDataEmailSender()

            # Run analysis (defaults to yesterday)
            results = {
                'zero_systems': analysis.check_zero_production_system_single_day(),
                'zero_inverters': analysis.check_zero_production_inverter_single_day(),
                'zero_granular': analysis.check_zero_production_granular_single_day(),
                'min_systems': analysis.check_minimum_production_system_single_day(),
                'dev_systems': analysis.check_production_deviation_systems(),
                'dev_inverters': analysis.check_production_deviation_inverters(),
                'dev_granular': analysis.check_production_deviation_granular()
            }

            # Create summary header
            today = date.today()
            # Get total counts from query results
            total_systems = results['dev_systems']['summary']['total_systems']
            total_inverters = results['dev_inverters']['summary']['total_inverters']
            total_granular = results['dev_granular']['summary']['total_devices']

            summary = f"""
{'='*60}
SOLAR PRODUCTION ANALYSIS REPORT
{'='*60}
Date: {today.strftime('%Y-%m-%d')}

ANALYSIS SUMMARY:
• Total Systems Analyzed: {total_systems}
• Total Inverters Analyzed: {total_inverters}
• Total Granular Devices Analyzed: {total_granular}
• Systems Below Quality Standards: {results['min_systems']['summary']['total_systems_below_standards']}

{'='*60}
"""
            # Generate text reports
            reports = [
                summary,
                # Zero production analysis
                reporter.translate_zero_production_results(results['zero_systems']),
                reporter.translate_zero_production_results(results['zero_inverters']),
                reporter.translate_zero_production_results(results['zero_granular']),
                # Minimum production analysis
                reporter.translate_minimum_production_results(results['min_systems']),
                # Deviation analysis
                reporter.translate_deviation_analysis_results(results['dev_systems']),
                reporter.translate_deviation_analysis_results(results['dev_inverters']),
                reporter.translate_deviation_analysis_results(results['dev_granular'])
            ]

            # Generate and send PDF
            pdf_path = pdf_gen.simple_report(reports)
            if pdf_path:
                email.send_pdf_report(pdf_path=pdf_path)
                pdf_gen.cleanup_temp_file(pdf_path)
                self.stdout.write(self.style.SUCCESS('Report generated and sent successfully'))
            else:
                raise Exception("Failed to generate PDF")

        except Exception as e:
            logger.error(f"Failed to generate daily report: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))