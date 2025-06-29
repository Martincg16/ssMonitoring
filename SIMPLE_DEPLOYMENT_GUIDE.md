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

## Step 10: Access Your Application

Your app will be available at:
```
http://YOUR_EC2_IP:8000
```

## Step 11: Set Up Cron Jobs for Data Collection

```bash
# Edit crontab
crontab -e

# Add these lines for daily data collection (runs at 6 AM and 7 AM)
0 6 * * * cd /opt/solar-monitoring/ssMonitoringProjectDJ && /opt/solar-monitoring/venv/bin/python manage.py solis_system_gen_yesterday
0 7 * * * cd /opt/solar-monitoring/ssMonitoringProjectDJ && /opt/solar-monitoring/venv/bin/python manage.py solis_inverter_gen_yesterday
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
- ✅ Restarts service and verifies deployment
- ✅ Tests both local and external access

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