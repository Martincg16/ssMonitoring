# SS Monitoring

_____________________
TO-DO

- Revisión de huawei al buscar los proyectos para traer los invesores y granular
- Completar instruccines de registro solis + registro solis

DÓNDE QUEDÉ
- Creación (más no revisón) de solisCrud def insert_solis_generacion_sistema_dia(data):


_____________________

A monitoring system for tracking and managing server status.

# Description

This project aims to provide a comprehensive solution for monitoring server status and performance metrics.

# How to

## Creating a new project
### Huawei
1. Look for the new project via Postman /stations via List plants
2. Add the plant manually to the database proyecto. Can be using PgAdmin or the Shell.
3. In the Shell run:
from solarDataNewSystem.register.huaweiRegister import register_and_fetch_huawei_history
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
fetcher = HuaweiFetcher()
token = fetcher.login()
station_code = 'NE=35123000'  # Replace with your actual code
inverters = register_and_fetch_huawei_history(token, station_code)
4. This creates the inverters. The MPPT will be created on their own by the fetcher + crud

### Solis
1. Look for any new project via solarDataFetch/solisApi.list_plants_api()
2. Add the plan manually to the database proyecto. Can be using pgAdmin or the Shell
3. In the shell run


## solarDataFetch Outputs
Solar data fetch will bring all the corresponsing plants from the inverter brand. In most occations working with batches.
### Solar system data daily
It must return a list of dictionaries resembling the following structure (not mandatory):
[ {'stationCode': 'NE=35759034', 'collectTime': 1747890000000, 'PVYield': 33.3} ]

### Solar inverter data daily
It must return a list of dictionaries resembling the following structure (not mandatory):

[{'identificador_inversor': 'NE=34096564', 'collectTime': 1747890000000, 'PVYield': 37.23}, {'identificador_inversor': 'NE=34096580', 'collectTime': 1747890000000, 'PVYield': 34.5}]

## solarDataStore how-to 

# Programming
## Stack
Django + Djangorestframework
Terraform
