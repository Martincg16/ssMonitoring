#!/bin/bash

# Solar Monitoring App - Automated EC2 Deployment Script
# This script follows Infrastructure as Code principles

set -e  # Exit on any error

echo "🚀 Starting Solar Monitoring App Deployment..."

# Configuration
EC2_IP=$(cd infrastructure/terraform && terraform output -raw ec2_public_ip)
SSH_KEY="$HOME/.ssh/id_rsa"
APP_NAME="solar-monitoring-app"
REMOTE_USER="ec2-user"

echo "📡 Deploying to EC2: $EC2_IP"

# Step 1: Clean up old deployment packages
echo "🧹 Cleaning up old deployment packages..."
rm -f solar-monitoring-app*.tar.gz

# Step 2: Create new deployment package
echo "📦 Creating deployment package..."
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='my_venv_1' \
    --exclude='infrastructure/terraform/.terraform' \
    --exclude='infrastructure/terraform/terraform.tfstate*' \
    -czf solar-monitoring-app.tar.gz \
    ssMonitoringProjectDJ/ \
    .env \
    infrastructure/

echo "✅ Package created: solar-monitoring-app.tar.gz"

# Step 3: Transfer package to EC2
echo "📤 Transferring package to EC2..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no solar-monitoring-app.tar.gz ${REMOTE_USER}@${EC2_IP}:~/

# Step 4: Deploy on EC2
echo "🔧 Deploying application on EC2..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${REMOTE_USER}@${EC2_IP} << 'EOF'
    set -e
    
    echo "📂 Extracting application files..."
    cd /opt/solar-monitoring
    tar -xzf ~/solar-monitoring-app.tar.gz
    
    echo "⚙️  Updating systemd service..."
    sudo cp infrastructure/systemd/solar-monitoring.service /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/solar-monitoring.service
    sudo systemctl daemon-reload
    
    echo "🔄 Restarting service..."
    sudo systemctl restart solar-monitoring
    
    echo "✅ Checking service status..."
    sudo systemctl status solar-monitoring --no-pager
    
    echo "🧪 Testing application..."
    sleep 3
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 || echo "❌ Local test failed"
    
    echo "🎉 Deployment completed!"
EOF

# Step 5: Final verification
echo "🌐 Testing external access..."
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${EC2_IP}:8000 || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! Application is running at: http://${EC2_IP}:8000"
else
    echo "⚠️  Application deployed but may need configuration check."
    echo "🔍 Access: http://${EC2_IP}:8000"
    echo "📋 Check logs with: sudo systemctl status solar-monitoring"
fi

echo "🎯 Deployment automation complete!" 