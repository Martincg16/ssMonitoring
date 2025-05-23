# SS Monitoring

A monitoring system for tracking and managing server status.

## Description

This project aims to provide a comprehensive solution for monitoring server status and performance metrics.

## How to

### Createing a new project
1. Look for the new project via Postman /stations
2. Add the plant manually to the database proyecto
3. In the Shell run:
from solarDataNewSystem.register.huaweiRegister import register_and_fetch_huawei_history
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
fetcher = HuaweiFetcher()
token = fetcher.login()
station_code = 'NE=35123000'  # Replace with your actual code
inverters = register_and_fetch_huawei_history(token, station_code)
4. This creates the inverters. The MPPT will be created on their own by the fetcher + crud