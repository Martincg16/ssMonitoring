import os
import sys
import django
from datetime import date, timedelta

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ssMonitoringProjectDJ.settings')
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5433'
django.setup()

# Import after Django setup
from solarDataReports.processes.analysis_engine import SolarDataAnalysis

def test_analysis_functions():
    analyzer = SolarDataAnalysis()
    yesterday = date.today() - timedelta(days=1)
    
    print("\n=== Testing Production Deviation Analysis ===")
    print(f"Analyzing deviations for {yesterday} compared to last 30 days")
    deviation_result = analyzer.check_production_deviation(yesterday)
    print("\nSystems with significant deviations:")
    if deviation_result['systems']:
        for system in deviation_result['systems']:
            print(f"\nSystem: {system['name']}")
            print(f"Current Production: {system['current_kwh']:.2f} kWh")
            print(f"Average Production: {system['avg_kwh']:.2f} kWh")
            print(f"Standard Deviation: {system['std_dev']:.2f}")
            print(f"Deviation: {system['deviation']:.2f} σ")
            print(f"Percent Difference: {system['percent_diff']:.1f}%")
    else:
        print("No significant deviations found")
    
    print(f"\nSummary:")
    print(f"Total systems checked: {deviation_result['summary']['total_systems']}")
    print(f"Systems with deviations: {deviation_result['summary']['systems_with_deviation']}")
    print(f"Comparison period: {deviation_result['summary']['comparison_period']['start']} to {deviation_result['summary']['comparison_period']['end']}")
    
    print("\n=== Testing System Level Analysis ===")
    system_result = analyzer.check_zero_production_system_single_day(yesterday)
    print(f"Systems with issues on {yesterday}:")
    print(system_result)
    
    print("\n=== Testing Inverter Level Analysis ===")
    inverter_result = analyzer.check_zero_production_inverter_single_day(yesterday)
    print(f"Inverters with issues on {yesterday}:")
    print(inverter_result)
    
    print("\n=== Testing Granular Level Analysis ===")
    granular_result = analyzer.check_zero_production_granular_single_day(yesterday)
    print(f"Granular devices with issues on {yesterday}:")
    print(granular_result)

if __name__ == '__main__':
    test_analysis_functions() 