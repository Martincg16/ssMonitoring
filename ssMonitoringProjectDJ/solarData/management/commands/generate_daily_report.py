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

            # Run detailed analysis (defaults to yesterday)
            self.stdout.write("Generating detailed analysis report...")
            results_detailed = {
                'zero_systems': analysis.check_zero_production_system_single_day(),
                'zero_inverters': analysis.check_zero_production_inverter_single_day(),
                'zero_granular': analysis.check_zero_production_granular_single_day(),
                'min_systems': analysis.check_minimum_production_system_single_day(),
                'dev_systems': analysis.check_production_deviation_systems(),
                'dev_inverters': analysis.check_production_deviation_inverters(),
                'dev_granular': analysis.check_production_deviation_granular()
            }

            # Create summary header for detailed report
            today = date.today()
            total_systems = results_detailed['dev_systems']['summary']['total_systems']
            total_inverters = results_detailed['dev_inverters']['summary']['total_inverters']
            total_granular = results_detailed['dev_granular']['summary']['total_devices']

            summary_detailed = f"""
{'='*60}
SOLAR PRODUCTION ANALYSIS REPORT
{'='*60}
Date: {today.strftime('%Y-%m-%d')}

ANALYSIS SUMMARY:
• Total Systems Analyzed: {total_systems}
• Total Inverters Analyzed: {total_inverters}
• Total Granular Devices Analyzed: {total_granular}
• Systems Below Quality Standards: {results_detailed['min_systems']['summary']['total_systems_below_standards']}

{'='*60}
"""
            # Generate text reports for detailed analysis
            reports_detailed = [
                summary_detailed,
                reporter.translate_zero_production_results(results_detailed['zero_systems']),
                reporter.translate_zero_production_results(results_detailed['zero_inverters']),
                reporter.translate_zero_production_results(results_detailed['zero_granular']),
                reporter.translate_minimum_production_results(results_detailed['min_systems']),
                reporter.translate_deviation_analysis_results(results_detailed['dev_systems']),
                reporter.translate_deviation_analysis_results(results_detailed['dev_inverters']),
                reporter.translate_deviation_analysis_results(results_detailed['dev_granular'])
            ]

            # Generate detailed PDF
            self.stdout.write("Creating detailed PDF...")
            pdf_path_detailed = pdf_gen.simple_report(reports_detailed)
            if not pdf_path_detailed:
                raise Exception("Failed to generate detailed PDF")

            # Run basic report analysis
            self.stdout.write("Generating basic report...")
            results_basic = {
                'no_target': analysis.check_systems_no_target(),
                'zero_systems': analysis.check_systems_zero_production_single_day(),
                'null_missing': analysis.check_systems_null_or_missing_single_day(),
                'under_target_15d': analysis.check_systems_under_target_15d(),
                'inverters_conditional': analysis.check_inverters_zero_conditional_single_day(),
                'granular_conditional': analysis.check_granular_zero_conditional_single_day()
            }

            # Get report date
            report_date = results_basic['zero_systems']['date']

            # Create summary for basic report
            summary_basic = f"""
{'='*60}
BASIC SOLAR PRODUCTION REPORT
{'='*60}
Generated on: {today.strftime('%Y-%m-%d')}
Analysis Date: {report_date}

SUMMARY OF ISSUES:
• Systems with no target defined: {results_basic['no_target']['summary']['total_count']}
• Systems with 0 production: {results_basic['zero_systems']['summary']['total_count']}
• Systems with null/missing data: {results_basic['null_missing']['summary']['total_count']}
• Systems under 15-day target: {results_basic['under_target_15d']['summary']['total_count']}
• Inverters with 0 (system produced): {results_basic['inverters_conditional']['summary']['total_count']}
• Granular with 0 (inverter produced): {results_basic['granular_conditional']['summary']['total_count']}

{'='*60}
"""

            # Generate text reports for basic report
            reports_basic = [
                summary_basic,
                reporter.translate_systems_no_target(results_basic['no_target']),
                reporter.translate_systems_zero_production(results_basic['zero_systems']),
                reporter.translate_systems_null_or_missing(results_basic['null_missing']),
                reporter.translate_systems_under_target_15d(results_basic['under_target_15d']),
                reporter.translate_inverters_zero_conditional(results_basic['inverters_conditional']),
                reporter.translate_granular_zero_conditional(results_basic['granular_conditional'])
            ]

            # Generate basic PDF
            self.stdout.write("Creating basic PDF...")
            pdf_path_basic = pdf_gen.simple_report(
                reports_basic,
                title="Basic Solar Production Report",
                date=report_date
            )
            if not pdf_path_basic:
                raise Exception("Failed to generate basic PDF")

            # Send both PDFs in one email
            self.stdout.write("Sending email with both reports...")
            pdf_attachments = [
                (pdf_path_detailed, f"solar_production_report_{report_date}.pdf"),
                (pdf_path_basic, f"basic_report_{report_date}.pdf")
            ]
            
            email_result = email.send_multiple_pdf_reports(
                pdf_paths=pdf_attachments,
                report_date=report_date
            )
            
            # Cleanup temp files
            pdf_gen.cleanup_temp_file(pdf_path_detailed)
            pdf_gen.cleanup_temp_file(pdf_path_basic)
            
            if email_result.get('success'):
                self.stdout.write(self.style.SUCCESS('Both reports generated and sent successfully'))
            else:
                self.stdout.write(self.style.WARNING(f"Reports generated but email failed: {email_result.get('error')}"))

        except Exception as e:
            logger.error(f"Failed to generate daily report: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))