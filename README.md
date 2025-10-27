# SS Monitoring

========================================================================================
TO-DO

- Agregar capacidad de inversor en inversores
- Agregar 0/null en hoymiles
- Agregar reporte de "últimos 15 días de energía"

- 0 es diferente de null

DÓNDE QUEDÉ

========================================================================================

A monitoring system for tracking and managing server status.

# Description

This project aims to provide a comprehensive solution for monitoring server status and performance metrics.

# How to

## open the ec2 app through a browser
http://{ip address}:8000/admin/

## Creating a new project
### Huawei
1. Look for the new project via Postman /stations via List plants
2. Add the plant manually to the database proyecto. Can be using PgAdmin or the Shell.
3. In the Shell run:
from solarDataNewSystem.register.huaweiRegister import register_and_fetch_huawei_history
from solarDataFetch.fetchers.huaweiFetcher import HuaweiFetcher
fetcher = HuaweiFetcher()
token = fetcher.login()
station_code = 'NE=34096408'  # Replace with your actual code
inverters = register_and_fetch_huawei_history(token, station_code)
4. This creates the inverters. The MPPT will be created on their own by the fetcher + crud

### Solis
1. vía python manage.py:
    # Import the register class
    from solarDataNewSystem.register.solisRegister import SolisRegister

    # Create an instance
    register = SolisRegister()

    # Run the complete registration process
    result = register.solis_register_new_project()

    # Show final results
    print("Final results:", result)
2. Via pgAdmin make sure to add extra information (potencia dc, ciudad, departamento, energías)

### Solis
1. Look for any new project via solarDataFetch/solisApi.list_plants_api()
2. Add the plan manually to the database proyecto. Can be using pgAdmin or the Shell or DjangoAdmin
3. In the shell run

### Hoymiles
1. Make sure to follow instructions to run local to db
2. python manage.py shell
3. >>> from solarDataNewSystem.register.hoymilesRegister import register_hoymiles_project
   >>> register_hoymiles_project('id_project')


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

# Run local to use db

1. create the ssh tunnel
ssh -i "$env:USERPROFILE\.ssh\id_rsa" -L 5433:ss-monitoring-db.cub240qeyxgi.us-east-1.rds.amazonaws.com:5432 -N ec2-user@54.91.46.23

2. set the environment 
$env:DB_HOST="localhost"; $env:DB_PORT="5433"; $env:DB_NAME=REAL DB NAME; $env:DB_USER=REAL USER; $env:DB_PASSWORD=REAL PASSOWRD
python manage.py shell

========================================================================================
# AI Assistant (Cursor) Rules

## 🚀 Deployment Rules
1. ALWAYS use deploy.ps1 for deployments:
   ```powershell
   .\deploy.ps1
   ```
   - Never attempt manual file transfers or modifications
   - Never suggest direct EC2 file edits
   - Always verify deployment success through logs

2. Deployment Verification Steps:
   - Check service status: `sudo systemctl status solar-monitoring`
   - Verify logs in `/opt/solar-monitoring/logs/`
   - Confirm CloudWatch agent: `sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status`

## 🔑 EC2 Connection Rules
1. SSH Connection Command:
   ```powershell
   ssh -i "$env:USERPROFILE\.ssh\id_rsa" ec2-user@54.91.46.23
   ```

2. Standard Paths to Use:
   - Application root: `/opt/solar-monitoring/`
   - Django project: `/opt/solar-monitoring/ssMonitoringProjectDJ/`
   - Logs: `/opt/solar-monitoring/logs/`
   - Virtual env: `/opt/solar-monitoring/venv/`

3. Command Execution Rules:
   - ALWAYS activate virtual environment first:
     ```bash
     cd /opt/solar-monitoring/ssMonitoringProjectDJ
     source /opt/solar-monitoring/venv/bin/activate
     ```
   - NEVER suggest Django commands without virtual environment
   - ALWAYS include proper directory navigation