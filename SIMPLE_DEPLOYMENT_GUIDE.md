# 🚀 Solar Monitoring App - Simple EC2 Deployment (No Gunicorn, No GitHub)

## Prerequisites
- Your EC2 instance is running with Amazon Linux 2023 (created via Terraform)
- RDS PostgreSQL database is accessible
- Your local code is ready to deploy with correct .env settings

## Step 1: Apply Updated Infrastructure

```bash
cd infrastructure/terraform
terraform apply
```
This will create a new EC2 instance with Amazon Linux 2023 and Python 3.11 support.

## Step 2: Get Your EC2 Connection Info

```bash
terraform output
```

Note down:
- `ec2_public_ip`: Your EC2 instance IP
- `rds_endpoint`: Your database endpoint
- `ssh_command`: SSH connection command

## Step 3: Prepare Your Local Files for Transfer

Create a deployment package (without .git):
```bash
# In your local ssMonitoring directory
# Remove any existing deployment packages
rm -f solar-monitoring-app*.tar.gz

# Create new deployment package
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='my_venv_1' -czf solar-monitoring-app.tar.gz ssMonitoringProjectDJ/ .env infrastructure/
```

## Step 4: Transfer Files to EC2

```bash
# Use the EC2 IP from terraform output
scp -i ~/.ssh/id_rsa solar-monitoring-app.tar.gz ec2-user@YOUR_EC2_IP:~/
```

## Step 5: Connect to EC2 Instance

```bash
# Use the EC2 IP from terraform output
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_EC2_IP
```

## Step 6: Verify Amazon Linux 2023 and Python

```bash
# Check OS version (should show Amazon Linux 2023)
cat /etc/os-release

# Check available Python versions
python3 --version        # Should show Python 3.9.x (system default)
python3.11 --version     # Should be available after dnf install
```

## Step 7: Set Up Application on EC2

```bash
# Create application directory
sudo mkdir -p /opt/solar-monitoring
sudo chown ec2-user:ec2-user /opt/solar-monitoring
cd /opt/solar-monitoring

# Extract your files
tar -xzf ~/solar-monitoring-app.tar.gz

# Install system dependencies (Amazon Linux 2023 uses dnf)
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip postgresql15
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3.11-devel postgresql15-devel

# Verify Python 3.11 installation
python3.11 --version  # Should show Python 3.11.12

# Create virtual environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# Verify you're using Python 3.11 in the virtual environment
python --version  # Should show Python 3.11.x

# Install Python dependencies
pip install --upgrade pip
pip install -r ssMonitoringProjectDJ/requirements.txt
```

**Note:** Your .env file should already have correct values from your local setup. No manual editing needed on the server.

## Step 8: Set Up Django Application

```bash
# Navigate to Django project
cd ssMonitoringProjectDJ

# Run migrations
python manage.py migrate

# Test the application
python manage.py runserver 0.0.0.0:8000
```

If the test works, press `Ctrl+C` to stop and continue to the next step.

## Step 9: Set Up systemd Service (Infrastructure as Code)

Copy the systemd service file from your deployment package:
```bash
# Copy the service file to systemd directory
sudo cp infrastructure/systemd/solar-monitoring.service /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/solar-monitoring.service

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable solar-monitoring
sudo systemctl start solar-monitoring

# Check service status
sudo systemctl status solar-monitoring
```

## Step 10: Set Up Automated Cron Jobs

The application includes automated Django cron jobs for daily data collection:

### Automatic Setup (via deploy.ps1)
The deployment script automatically:
- ✅ Installs cron service (`cronie`)
- ✅ Enables and starts the cron daemon
- ✅ Reads `CRONJOBS` configuration from `settings.py`
- ✅ Adds/updates cron jobs automatically

### Manual Cron Job Management (if needed)

```bash
# Install cron service (already done by deploy.ps1)
sudo yum install -y cronie
sudo systemctl enable crond
sudo systemctl start crond

# Navigate to Django project
cd /opt/solar-monitoring/ssMonitoringProjectDJ
source ../venv/bin/activate

# Add cron jobs from settings.py
python manage.py crontab add

# View active cron jobs
python manage.py crontab show

# View system crontab
crontab -l

# Remove all Django cron jobs
python manage.py crontab remove
```

### Current Cron Configuration

In `ssMonitoringProjectDJ/ssMonitoringProjectDJ/settings.py`:
```python
CRONJOBS = [
    # Run daily data collection at 10:10 AM Colombian time (15:10 UTC)
    ('10 15 * * *', 'django.core.management.call_command', ['collect_all_gen_yesterday', '--skip-errors']),
]
```

### How to Modify Cron Schedule

1. **Edit the time in `settings.py`:**
   ```python
   # Format: minute hour day month day_of_week
   ('10 15 * * *', 'django.core.management.call_command', ['collect_all_gen_yesterday']),
   #   ^  ^
   #   |  +-- Hour (0-23, UTC time)
   #   +----- Minute (0-59)
   ```

2. **Common schedule examples:**
   ```python
   # Every day at 3:00 AM Colombian time (8:00 AM UTC)
   ('0 8 * * *', 'django.core.management.call_command', ['collect_all_gen_yesterday']),
   
   # Every day at midnight Colombian time (5:00 AM UTC)
   ('0 5 * * *', 'django.core.management.call_command', ['collect_all_gen_yesterday']),
   
   # Every hour
   ('0 * * * *', 'django.core.management.call_command', ['collect_all_gen_yesterday']),
   ```

3. **Deploy the changes:**
   ```bash
   .\deploy.ps1  # This will automatically update the cron jobs
   ```

### Troubleshooting Cron Jobs

```bash
# Check if cron daemon is running
sudo systemctl status crond

# View cron logs
sudo tail -f /var/log/cron

# Test management command manually
cd /opt/solar-monitoring/ssMonitoringProjectDJ
source ../venv/bin/activate
python manage.py collect_all_gen_yesterday

# Check Django logs for cron job execution
cat /opt/solar-monitoring/logs/django.log
```

## Step 11: Access Your Application

Your app will be available at:
```
http://YOUR_EC2_IP:8000
```

## 🔧 Management Commands

```bash
# Check service status
sudo systemctl status solar-monitoring

# View logs
sudo journalctl -u solar-monitoring -f

# Restart service
sudo systemctl restart solar-monitoring

# Stop service
sudo systemctl stop solar-monitoring

# Start service
sudo systemctl start solar-monitoring
```

## Step 12: CloudWatch Logging Configuration (CRITICAL)

The application includes organized CloudWatch logging that automatically separates logs by component:

### Organized Log Structure

The deployment automatically creates:
- **`/aws/ssmonitoring/django/solarDataFetch`** with streams:
  - `Huawei` - All Huawei API operations and data fetching
  - `Solis` - All Solis API operations and data fetching
- **`/aws/ssmonitoring/django/Commands`** with stream:
  - `management-commands` - Command orchestration and general operations

### Log File Organization

Local log files on EC2:
```bash
/opt/solar-monitoring/logs/
├── huawei_fetcher.log     → CloudWatch: /aws/ssmonitoring/django/solarDataFetch (Huawei stream)
├── solis_fetcher.log      → CloudWatch: /aws/ssmonitoring/django/solarDataFetch (Solis stream)
└── django_general.log     → CloudWatch: /aws/ssmonitoring/django/Commands (management-commands stream)
```

### CloudWatch Configuration

The deployment script automatically:
✅ **Copies CloudWatch configuration** from `infrastructure/cloudwatch-config.json`  
✅ **Stops and restarts CloudWatch agent** with new configuration  
✅ **Verifies agent status** and reports success/failure  
✅ **Creates organized log groups and streams** automatically  

### Troubleshooting CloudWatch

If CloudWatch logging is not working:

```bash
# Check CloudWatch agent status
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status -m ec2

# Check agent logs
sudo tail -f /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log

# Manually reconfigure CloudWatch (if needed)
sudo cp /opt/solar-monitoring/infrastructure/cloudwatch-config.json /opt/aws/amazon-cloudwatch-agent/etc/
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json -s

# Verify local log files are being created
ls -la /opt/solar-monitoring/logs/
tail -f /opt/solar-monitoring/logs/huawei_fetcher.log
```

### Log Format Benefits

Each log entry includes the component and function for easy filtering:
- **Huawei**: `|HuaweiFetcher|login|`, `|HuaweiFetcher|fetch_huawei_generacion_sistema_dia|`
- **Solis**: `|SolisFetcher|fetch_solis_generacion_sistema_dia|`, `|SolisFetcher|fetch_solis_generacion_un_inversor_dia|`
- **Commands**: Standard Django logging with command orchestration

This allows you to filter logs in CloudWatch by searching for specific components or functions.

## 🔄 Updating Your Application

### Option A: Automated Deployment (Recommended)

**One command deployment:**
```bash
# Linux/Mac/WSL/Git Bash
bash deploy_to_ec2.sh
```

**What the script does:**
- ✅ Gets EC2 IP from Terraform output automatically
- ✅ Cleans up old deployment packages
- ✅ Creates new deployment package with latest code
- ✅ Transfers to EC2 via SCP
- ✅ Extracts files and updates systemd service
- ✅ **Automatically installs and configures cron jobs**
- ✅ **Updates cron schedule from settings.py**
- ✅ Restarts service and verifies deployment
- ✅ Tests both local and external access
- ✅ **Verifies cron job setup**

### Option B: Manual Deployment

When you make changes to your code:

1. **Update files locally** (including .env if needed)

2. **Create new deployment package locally:**
```bash
# Remove any existing deployment packages
rm -f solar-monitoring-app*.tar.gz

# Create new deployment package
tar --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='my_venv_1' -czf solar-monitoring-app.tar.gz ssMonitoringProjectDJ/ .env infrastructure/
```

3. **Transfer to EC2:**
```bash
scp -i ~/.ssh/id_rsa solar-monitoring-app.tar.gz ec2-user@YOUR_EC2_IP:~/
```

4. **Update on EC2:**
```bash
ssh -i ~/.ssh/id_rsa ec2-user@YOUR_EC2_IP
cd /opt/solar-monitoring
tar -xzf ~/solar-monitoring-app.tar.gz
sudo systemctl restart solar-monitoring
```

## 🔍 Troubleshooting

### Check Python Versions
```bash
# System Python (should be 3.9)
python3 --version

# Python 3.11 (should be 3.11.12)
python3.11 --version

# In virtual environment (should be 3.11)
source /opt/solar-monitoring/venv/bin/activate
python --version
```

### Database Connection Issues
```bash
# Test database connection
cd /opt/solar-monitoring/ssMonitoringProjectDJ
source ../venv/bin/activate
python manage.py dbshell
```

### View Application Logs
```bash
# Real-time logs
sudo journalctl -u solar-monitoring -f

# Recent logs
sudo journalctl -u solar-monitoring --since "1 hour ago"
```

## Key Differences from Amazon Linux 2:
- Package manager: `yum` → `dnf`
- Python: Uses `python3.11` specifically for Django 5.2 compatibility
- Virtual environment: Must use `python3.11 -m venv` for proper Python version

## 🚀 Advantages of This Approach

✅ **Simple**: Minimal setup, easy to understand  
✅ **No GitHub needed**: Direct file transfer  
✅ **No complex servers**: Just Django  
✅ **Easy updates**: Simple file replacement  
✅ **Full Django features**: All your management commands work  
✅ **Automatic restart**: systemd handles crashes  
✅ **Easy monitoring**: Standard systemd logging 