#!/usr/bin/env python3
"""
Test script to capture raw API response for Hoymiles plant/inverter
Plant ID: 617280, Inverter: 116580137313
"""

import os
import sys
import django
import json
from datetime import datetime

# Add the project directory to Python path
sys.path.append('.')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ssMonitoringProjectDJ.settings')
django.setup()

from solarDataFetch.fetchers.hoymilesFetcher import HoymilesFetcher

def test_api_response():
    """Capture the raw API response for analysis"""
    
    fetcher = HoymilesFetcher()
    plant_id = '617280'
    inverter_sn = '116580137313'
    target_date = '2025-09-24'
    
    print(f'Testing Hoymiles API for:')
    print(f'Plant ID: {plant_id}')
    print(f'Inverter: {inverter_sn}')
    print(f'Date: {target_date}')
    print('='*80)
    
    # Construct URL and body manually to capture raw response
    endpoint = f"v2/query/{plant_id}/{inverter_sn}/mi_data_day"
    body = {"date": target_date}
    
    print(f'API Endpoint: {fetcher.base_url}/{endpoint}')
    print(f'Request Body: {json.dumps(body)}')
    print('='*80)
    
    try:
        # Make the raw API request
        response_data = fetcher._make_request(endpoint, body)
        
        # Save raw response to file
        with open('hoymiles_raw_response.json', 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        
        print('✅ Raw API response saved to: hoymiles_raw_response.json')
        print()
        
        # Print summary info
        if response_data and 'data' in response_data:
            data_array = response_data['data']
            print(f'Response status: {response_data.get("status")}')
            print(f'Response message: {response_data.get("message")}')
            print(f'Number of time entries: {len(data_array)}')
            
            if data_array:
                print()
                print('First 3 entries:')
                for i, entry in enumerate(data_array[:3]):
                    print(f'Entry {i+1}: {json.dumps(entry, ensure_ascii=False)}')
                
                print()
                print('Last 3 entries:')
                for i, entry in enumerate(data_array[-3:], len(data_array)-2):
                    print(f'Entry {i}: {json.dumps(entry, ensure_ascii=False)}')
                
                # Check for any non-zero values
                print()
                print('Checking for non-zero values...')
                non_zero_found = False
                for entry in data_array:
                    dc_array = entry.get('dc', [])
                    for dc_entry in dc_array:
                        tp_value = dc_entry.get('tp', 0)
                        if tp_value > 0:
                            print(f'Found non-zero tp value: {tp_value} at time {entry.get("time")}')
                            non_zero_found = True
                            break
                    if non_zero_found:
                        break
                
                if not non_zero_found:
                    print('❌ All tp values are 0 - this explains why PVYield is 0.0')
                
            else:
                print('❌ Data array is empty')
        else:
            print('❌ No data in response')
            
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_response()
