# Acá hay una lista de errores comunes y cómo arreglarlos

## Huawei Login token failed
1. Revisar si la falla fue a nivel sistema, inversor o granular (o varios)
2. ssh steps
- ssh -i ~/.ssh/id_rsa ec2-user@{ip address} - http://54.91.46.23/
- cd /opt/solar-monitoring/ssMonitoringProjectDJ
- source /opt/solar-monitoring/venv/bin/activate
- python manage.py huawei_{inverter}_gen --date aaaa-mm-dd