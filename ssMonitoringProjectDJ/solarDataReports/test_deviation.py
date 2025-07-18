"""
Test script for production deviation analysis
"""

import os
import sys
import django
from datetime import date, timedelta
import json

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ssMonitoringProjectDJ.settings')
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5433'
django.setup()

from solarDataReports.processes.analysis_engine import SolarDataAnalysis

def format_system_output(system):
    """Formats a single system's deviation data for display"""
    return (
        f"\nSystem: {system['name']}\n"
        f"  Current Production: {system['current_kwh']:.2f} kWh\n"
        f"  Average Production: {system['avg_kwh']:.2f} kWh\n"
        f"  Standard Deviation: {system['std_dev']:.2f}\n"
        f"  Deviation: {system['deviation']:.2f} σ\n"
        f"  Percent Difference: {system['percent_diff']:.1f}%\n"
        f"  Days Analyzed: {system['days_analyzed']}"
    )

def test_deviation_analysis(test_date=None):
    """
    Tests the production deviation analysis for solar systems
    
    Args:
        test_date (date, optional): Specific date to test. Defaults to yesterday.
    """
    analyzer = SolarDataAnalysis()
    
    # Use yesterday if no date provided
    analysis_date = test_date if test_date else date.today() - timedelta(days=1)
    print(f"\nAnalyzing production deviations for {analysis_date}")
    
    # Run the analysis
    result = analyzer.check_production_deviation_systems(analysis_date)
    
    # Display results
    print("\n=== Systems with Significant Deviations ===")
    if result['systems']:
        for system in result['systems']:
            print(format_system_output(system))
    else:
        print("No significant deviations found")
    
    print(f"\n=== Analysis Summary ===")
    print(f"Total systems analyzed: {result['summary']['total_systems']}")
    print(f"Systems with deviations: {result['summary']['systems_with_deviation']}")
    print(f"Analysis period: {result['summary']['comparison_period']['start']} to {result['summary']['comparison_period']['end']}")
    print(f"Maximum days of data available: {result['summary']['comparison_period']['days_available']}")

if __name__ == '__main__':
    # Get test date from command line if provided (format: YYYY-MM-DD)
    if len(sys.argv) > 1:
        try:
            year, month, day = map(int, sys.argv[1].split('-'))
            test_date = date(year, month, day)
        except (ValueError, IndexError):
            print("Invalid date format. Use: YYYY-MM-DD")
            sys.exit(1)
    else:
        test_date = None
    
    test_deviation_analysis(test_date) 