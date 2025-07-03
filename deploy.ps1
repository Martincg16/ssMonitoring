# Solar Monitoring App - PowerShell Deployment Script
# Optimized for PowerShell environment

Write-Host "Starting Solar Monitoring App Deployment..." -ForegroundColor Green

# Configuration
Push-Location infrastructure/terraform
$EC2_IP = terraform output -raw ec2_public_ip
Pop-Location

$SSH_KEY = "$env:USERPROFILE\.ssh\id_rsa"
$REMOTE_USER = "ec2-user"

Write-Host "Deploying to EC2: $EC2_IP" -ForegroundColor Cyan

# Step 1: Clean up old deployment packages
Write-Host "Cleaning up old deployment packages..." -ForegroundColor Yellow
Remove-Item -Path "solar-monitoring-app*" -Force -ErrorAction SilentlyContinue

# Step 2: Create new deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
Compress-Archive -Path "ssMonitoringProjectDJ", ".env", "infrastructure" -DestinationPath "solar-monitoring-app.zip" -Force

Write-Host "Package created: solar-monitoring-app.zip" -ForegroundColor Green

# Step 3: Transfer package to EC2
Write-Host "Transferring package to EC2..." -ForegroundColor Yellow
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no solar-monitoring-app.zip ${REMOTE_USER}@${EC2_IP}:~/

# Step 4: Deploy on EC2 - Using multiple SSH commands instead of complex script
Write-Host "Deploying application on EC2..." -ForegroundColor Yellow

# Setup directories
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "sudo mkdir -p /opt/solar-monitoring && sudo chown ec2-user:ec2-user /opt/solar-monitoring"

# Install basic dependencies and setup application
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "sudo yum install -y unzip python3.11 python3.11-pip"

# Create logs directory first
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring && mkdir -p logs && chmod 755 logs"

# Extract files
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring && unzip -o -q ~/solar-monitoring-app.zip"

# Setup virtual environment
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring && rm -rf venv && python3.11 -m venv venv"

# Install dependencies
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring && source venv/bin/activate && cd ssMonitoringProjectDJ && python -m pip install --upgrade pip && pip install -r requirements.txt"

# Check database before migrations
Write-Host "Checking database before migrations..." -ForegroundColor Yellow
$CHECK_DB = ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring/ssMonitoringProjectDJ && source ../venv/bin/activate && python manage.py shell -c 'from solarData.models import Proyecto; print(Proyecto.objects.count())'"

if ($CHECK_DB -gt 0) {
    Write-Host "WARNING: Database contains $CHECK_DB projects!" -ForegroundColor Red
    $CONTINUE = Read-Host "Do you want to continue with the deployment? (yes/no)"
    if ($CONTINUE -ne "yes") {
        Write-Host "Deployment aborted." -ForegroundColor Red
        exit 1
    }
}

# Run migrations with --fake-initial to prevent data loss
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring && source venv/bin/activate && cd ssMonitoringProjectDJ && python manage.py migrate --fake-initial"

# Setup systemd service
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "cd /opt/solar-monitoring && sudo cp infrastructure/systemd/solar-monitoring.service /etc/systemd/system/ && sudo chmod 644 /etc/systemd/system/solar-monitoring.service && sudo systemctl daemon-reload"

# Start service
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "sudo systemctl restart solar-monitoring"

# Check status
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "sudo systemctl status solar-monitoring --no-pager"

# Step 5: Final verification
Write-Host "Testing external access..." -ForegroundColor Yellow
Start-Sleep 2
$HTTP_CODE = try { (Invoke-WebRequest -Uri "http://${EC2_IP}:8000" -UseBasicParsing -TimeoutSec 10).StatusCode } catch { 0 }

if ($HTTP_CODE -eq 200) {
    Write-Host "SUCCESS! Application is running at: http://${EC2_IP}:8000" -ForegroundColor Green
} else {
    Write-Host "Application deployed but may need configuration check." -ForegroundColor Yellow
    Write-Host "Access: http://${EC2_IP}:8000" -ForegroundColor Cyan
    Write-Host "Check logs with: sudo systemctl status solar-monitoring" -ForegroundColor Cyan
}

# Step 6: Verify logging and CloudWatch setup
Write-Host "Verifying logging and CloudWatch setup..." -ForegroundColor Yellow
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} "echo '=== Application Logs ===' && ls -la /opt/solar-monitoring/logs/ && echo '=== Django Log Content ===' && cat /opt/solar-monitoring/logs/django.log 2>/dev/null || echo 'No logs yet' && echo -e '\n=== CloudWatch Agent Status ===' && sudo systemctl is-active amazon-cloudwatch-agent && echo 'CloudWatch Agent is running and sending logs to AWS CloudWatch /aws/solar-monitoring/django'"

Write-Host "Deployment automation complete!" -ForegroundColor Green 