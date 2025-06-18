# Solar Monitoring Infrastructure

## Overview
Terraform configuration for deploying the Solar Monitoring Django application on AWS using Free Tier resources.

## Architecture
- **VPC**: Custom VPC with public and private subnets
- **EC2**: t2.micro instance running Amazon Linux 2023
- **RDS**: PostgreSQL database (db.t3.micro) publicly accessible for development
- **Security**: Security groups configured for PostgreSQL and Django access

## Recent Updates (Based on AWS Documentation Review)

### ✅ Updated for Current AWS Best Practices
- **RDS Instance Class**: Changed from `db.t2.micro` to `db.t3.micro`
  - Reason: db.t2.micro is deprecated for PostgreSQL
  - db.t3.micro is still Free Tier eligible and offers better performance
- **PostgreSQL Version**: Updated from 17.4 to 16.8
  - Reason: Better long-term support and stability
  - 16.8 is actively maintained with regular security updates through March 2026
- **EC2 User Data**: Added PostgreSQL client tools installation

### Free Tier Compliance ✅
- EC2: t2.micro (750 hours/month free)
- RDS: db.t3.micro (750 hours/month free)
- Storage: 20GB gp2 (within 20GB free tier limit)
- No encryption (not available in free tier)
- No backups (to avoid charges)

## Prerequisites
1. AWS CLI configured with appropriate credentials
2. Terraform installed (version 1.0+)
3. Environment variables set:
   ```bash
   export TF_VAR_db_password="your_secure_password"
   ```

## Deployment
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Database Connection
After deployment, you can connect to the PostgreSQL database using:
- **Host**: (from terraform output `rds_endpoint`)
- **Port**: 5432
- **Database**: ssmonitoring
- **Username**: postgres
- **Password**: (your TF_VAR_db_password)

## Cost Optimization
This configuration is designed to stay within AWS Free Tier limits:
- No charges expected for compute and database (within 750 hours/month)
- No charges for storage (within 20GB limit)
- No charges for data transfer (minimal expected)

## Security Notes
- RDS is publicly accessible for development/pgAdmin access
- Security groups restrict access to PostgreSQL port (5432)
- Consider adding IP restrictions for production use

## What This Creates

- **VPC**: 10.0.0.0/16 with public and private subnets
- **EC2 Instance**: t2.micro (FREE TIER) for development
- **RDS PostgreSQL**: db.t2.micro (FREE TIER) in private subnet
- **Security Groups**: Minimal access controls
- **Key Pair**: For SSH access to EC2

## Setup Steps

### 1. Create SSH Key (if you don't have one)
```bash
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa
```

### 2. Configure Environment Variables
```bash
# From the root directory (ssMonitoring/)
cp env.example .env
```

Edit `.env` and set your database password:
```
TF_VAR_db_password=your-secure-password-here
```

### 3. Load Environment Variables and Deploy
```bash
# Load environment variables (from root directory)
source .env

# Go to terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Create the infrastructure
terraform apply
```

### 4. Get Connection Information
After deployment, Terraform will output:
- EC2 public IP address
- RDS endpoint
- SSH command to connect

## Costs (AWS Free Tier)

- **EC2 t2.micro**: FREE (750 hours/month)
- **RDS db.t2.micro**: FREE (750 hours/month)
- **Storage**: FREE (20GB RDS + 30GB EBS)
- **Network**: FREE (15GB transfer)
- **Total**: $0/month (within free tier limits)

## Next Steps

After infrastructure is created:
1. SSH to EC2 instance
2. Clone your Django repository
3. Configure Django to use the RDS database
4. Deploy and run your application

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**⚠️ This will permanently delete all data!** 