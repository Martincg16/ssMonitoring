# Solar Monitoring Infrastructure - Simple Production Setup
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Data source for latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "ss-monitoring-vpc"
    Environment = "dev"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "ss-monitoring-igw"
    Environment = "dev"
  }
}

# Public Subnet (for EC2)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name        = "ss-monitoring-public-subnet"
    Environment = "dev"
  }
}

# Private Subnet 1 (for RDS)
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name        = "ss-monitoring-private-subnet-1"
    Environment = "dev"
  }
}

# Private Subnet 2 (for RDS - required for subnet group)
resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name        = "ss-monitoring-private-subnet-2"
    Environment = "dev"
  }
}

# Route Table for Public Subnet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "ss-monitoring-public-rt"
    Environment = "dev"
  }
}

# Route Table Association for Public Subnet
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group for EC2 (Django App)
resource "aws_security_group" "ec2" {
  name        = "ss-monitoring-ec2-sg"
  description = "Security group for Solar Monitoring EC2 instance"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Django app port (for development access only)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict this to your IP later
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ss-monitoring-ec2-sg"
    Environment = "dev"
  }
}

# Security Group for RDS - Allows all access for pgAdmin
resource "aws_security_group" "rds" {
  name        = "ss-monitoring-rds-sg"
  description = "Security group for Solar Monitoring RDS instance"
  vpc_id      = aws_vpc.main.id

  # Allow PostgreSQL access from EC2
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  # Allow PostgreSQL access from anywhere (for local pgAdmin)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "PostgreSQL access from anywhere for pgAdmin"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ss-monitoring-rds-sg"
    Environment = "dev"
  }
}

# Key Pair (commented out for now - uncomment when you have SSH keys)
resource "aws_key_pair" "main" {
  key_name   = "ss-monitoring-key"  
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDJRr8uzoidJLuoj2WaR9KdniUlpohAO3EYorWC9PuZIyNRjCHx9WZcAPZb86d6VBfxmB6PDZqIps99bB+6EmpQfg8lIEaY1tIT9S2Weksn7a49zqS39KNwtfrAGQyw37IHACoTQ+lv184NVcbs7mkvFouORHTO+g9bmb1lgM+bs155m2unBlU1EJDAtFsVJKlyw/ehscwyr4aHq1p4ajz1Z2lVtqv5m0B3Syz7j4KOTOERxtgduecrmF7nbeGuo39bH1eNyQferO/YLDTIDPybIe9QnGyvdlUcnjZM2pxB3bRJG7xynhoY9UEhGwrSnCykhHmxBl6miJZWyEM0W+0NcmMDtCnq54k60DXiLA3GO6DWwHJCuOtoL+6ZjwihTJMdur8asscB443e3WoumRZ0oGrFdEbP0Or3XwAutxTQ8gyTZ4Mjg4QEUR9vxz3A42v/apHDua0Mk9fXZoGU6XT/FS2bZGoZe74DRDgDM8Kpxc56U4I2lUTQ6rehv1EWmXu9qsSeULJ+ne0uE6ccWEa1H/M4bCNB4ChtHXbLZPJjCrLI9/eMO7cuEt4zjt90wOu7MMTNRIxFDuI+kdxBaDCsSw+OR2u0mcQCBzjK22qT6twDE8QPyOBrsXq1x9eGlcSNAHm3dzXhQwNtNF01879iq/4UmNPA94XGuOY5FZgGWQ== martin@rocasol.com.co"

  tags = {
    Name        = "ss-monitoring-key"
    Environment = "dev"
  }
}

# IAM Role for EC2 CloudWatch permissions
resource "aws_iam_role" "ec2_cloudwatch_role" {
  name = "ss-monitoring-ec2-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "ss-monitoring-ec2-cloudwatch-role"
    Environment = "dev"
  }
}

# IAM policy for CloudWatch logs
resource "aws_iam_role_policy" "ec2_cloudwatch_policy" {
  name = "ss-monitoring-ec2-cloudwatch-policy"
  role = aws_iam_role.ec2_cloudwatch_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups",
          "ssm:GetParameter",
          "ssm:PutParameter",
          "ssm:DescribeParameters",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      }
    ]
  })
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ss-monitoring-ec2-profile"
  role = aws_iam_role.ec2_cloudwatch_role.name

  tags = {
    Name        = "ss-monitoring-ec2-profile"
    Environment = "dev"
  }
}

# CloudWatch Log Group for Django application logs
resource "aws_cloudwatch_log_group" "django_logs" {
  name              = "/aws/solar-monitoring/django"
  retention_in_days = 7

  tags = {
    Name        = "ss-monitoring-django-logs"
    Environment = "dev"
  }
}

# EC2 Instance (Free Tier)
resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "t2.micro"
  key_name              = aws_key_pair.main.key_name
  subnet_id             = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = <<-EOF
#!/bin/bash
# Enable logging
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting user-data script execution at $(date)"

# Update system and wait for completion
echo "Updating system packages..."
dnf update -y
while pgrep -f dnf > /dev/null; do
    echo "Waiting for package manager to finish..."
    sleep 5
done

# Install CloudWatch Agent first
echo "Installing CloudWatch Agent..."
dnf install -y amazon-cloudwatch-agent
if [ $? -ne 0 ]; then
    echo "Failed to install CloudWatch Agent. Retrying..."
    sleep 10
    dnf install -y amazon-cloudwatch-agent
fi

# Create app directory structure
echo "Creating application directories..."
mkdir -p /opt/solar-monitoring/logs
chown -R ec2-user:ec2-user /opt/solar-monitoring
chmod 755 /opt/solar-monitoring/logs

# Create initial log file with proper permissions
touch /opt/solar-monitoring/logs/django.log
chown ec2-user:ec2-user /opt/solar-monitoring/logs/django.log
chmod 664 /opt/solar-monitoring/logs/django.log

# Create CloudWatch agent config
echo "Configuring CloudWatch Agent..."
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOL'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/solar-monitoring/logs/django.log",
            "log_group_name": "/aws/solar-monitoring/django",
            "log_stream_name": "django-{instance_id}",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/solar-monitoring/django",
            "log_stream_name": "user-data-{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOL

# Start CloudWatch agent
echo "Starting CloudWatch Agent..."
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

# Enable and start CloudWatch agent
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Install other required packages
echo "Installing Python and other dependencies..."
dnf install -y python3.11 python3.11-pip git

# Create symlinks for easier access
ln -sf /usr/bin/python3.11 /usr/local/bin/python3
ln -sf /usr/bin/pip3.11 /usr/local/bin/pip3

# Final status check
systemctl status amazon-cloudwatch-agent --no-pager

echo "User-data script completed at $(date)"
EOF

  tags = {
    Name        = "ss-monitoring-app"
    Environment = "dev"
  }
}

# Public Subnet 2 (for RDS - needs to be in different AZ for subnet group)
resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.4.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name        = "ss-monitoring-public-subnet-2"
    Environment = "dev"
  }
}

# Route Table Association for Public Subnet 2
resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# RDS Subnet Group - Using public subnets for internet access
resource "aws_db_subnet_group" "main" {
  name       = "ss-monitoring-subnet-group"
  subnet_ids = [aws_subnet.public.id, aws_subnet.public_2.id]

  tags = {
    Name        = "ss-monitoring-subnet-group"
    Environment = "dev"
  }
}

# RDS Parameter Group for audit logging
resource "aws_db_parameter_group" "postgres" {
  family = "postgres16"
  name   = "ss-monitoring-postgres16-params"

  parameter {
    name  = "log_statement"
    value = "mod"  # Log all DML (INSERT, UPDATE, DELETE) and DDL (CREATE, ALTER, etc.)
    apply_method = "immediate"
  }

  parameter {
    name  = "log_filename"
    value = "postgresql-%Y-%m-%d_%H.log"  # Daily log files
    apply_method = "immediate"
  }

  parameter {
    name  = "log_connections"
    value = "1"  # Log all connections
    apply_method = "immediate"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"  # Log all disconnections
    apply_method = "immediate"
  }

  parameter {
    name  = "log_rotation_age"
    value = "1440"  # Rotate logs daily (in minutes)
    apply_method = "immediate"
  }

  parameter {
    name  = "log_rotation_size"
    value = "10240"  # Also rotate if size exceeds 10MB
    apply_method = "immediate"
  }

  parameter {
    name  = "log_destination"
    value = "csvlog"  # Use CSV format for better parsing
    apply_method = "immediate"
  }

  tags = {
    Name        = "ss-monitoring-postgres-params"
    Environment = "dev"
  }
}

# RDS Instance (Free Tier) - Publicly accessible for pgAdmin
resource "aws_db_instance" "postgres" {
  identifier                = "ss-monitoring-db"
  engine                    = "postgres"
  engine_version            = "16.8"
  instance_class            = "db.t3.micro" # Free tier eligible
  allocated_storage         = 20 # Free tier: 20GB
  storage_type              = "gp2"
  storage_encrypted         = false # Encryption not available in free tier

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # Make publicly accessible for local pgAdmin connection
  publicly_accessible = true

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  skip_final_snapshot = false # Changed to false to ensure a final snapshot is taken
  final_snapshot_identifier = "ss-monitoring-final-snapshot"
  deletion_protection = true # Enable deletion protection

  backup_retention_period = 1 # Minimum backup retention while staying in free tier
  backup_window = "03:00-04:00" # Early morning UTC backup window
  
  # Enhanced monitoring and insights
  monitoring_interval = 60  # Free tier allows 60-second intervals
  monitoring_role_arn = aws_iam_role.rds_monitoring_role.arn
  performance_insights_enabled = true  # Free tier includes 7 days retention
  performance_insights_retention_period = 7  # Days, free tier maximum

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]  # Export PostgreSQL logs to CloudWatch

  parameter_group_name = aws_db_parameter_group.postgres.name

  tags = {
    Name        = "ss-monitoring-db"
    Environment = "dev"
  }

  # Prevent terraform from destroying the database
  lifecycle {
    prevent_destroy = true
  }
}

# IAM role for RDS enhanced monitoring
resource "aws_iam_role" "rds_monitoring_role" {
  name = "ss-monitoring-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "ss-monitoring-rds-monitoring-role"
    Environment = "dev"
  }
}

# Attach the AWS managed policy for RDS enhanced monitoring
resource "aws_iam_role_policy_attachment" "rds_monitoring_policy" {
  role       = aws_iam_role.rds_monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Log Group for RDS logs with daily streams
resource "aws_cloudwatch_log_group" "rds_logs" {
  name              = "/aws/rds/instance/ss-monitoring-db/postgresql"
  retention_in_days = 7  # Free tier friendly retention

  tags = {
    Name        = "ss-monitoring-rds-logs"
    Environment = "dev"
    LogRotation = "daily"
  }
}

# Metric filter for CRUD operations
resource "aws_cloudwatch_log_metric_filter" "crud_operations" {
  name           = "crud-operations"
  pattern        = "[timestamp=*] INSERT|UPDATE|DELETE|CREATE|ALTER|DROP"
  log_group_name = aws_cloudwatch_log_group.rds_logs.name

  metric_transformation {
    name      = "CRUDOperationsCount"
    namespace = "CustomMetrics/Database"
    value     = "1"
  }
}

# Metric filter for connections/disconnections
resource "aws_cloudwatch_log_metric_filter" "connection_events" {
  name           = "connection-events"
  pattern        = "[timestamp=*] connection received|disconnection complete"
  log_group_name = aws_cloudwatch_log_group.rds_logs.name

  metric_transformation {
    name      = "ConnectionEventsCount"
    namespace = "CustomMetrics/Database"
    value     = "1"
  }
}

# CloudWatch Metric Alarms for database monitoring
resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "ss-monitoring-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "DatabaseConnections"
  namespace          = "AWS/RDS"
  period             = "300"  # 5 minutes
  statistic          = "Average"
  threshold          = "80"  # 80% of max connections
  alarm_description  = "This metric monitors database connections"
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  alarm_actions = []  # You can add SNS topic ARNs here for notifications
  ok_actions    = []  # You can add SNS topic ARNs here for notifications

  tags = {
    Name        = "ss-monitoring-db-connections-alarm"
    Environment = "dev"
  }
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "ss-monitoring-db-storage-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "FreeStorageSpace"
  namespace          = "AWS/RDS"
  period             = "300"  # 5 minutes
  statistic          = "Average"
  threshold          = "2147483648"  # 2GB free space (in bytes)
  alarm_description  = "This metric monitors free storage space"
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  alarm_actions = []  # You can add SNS topic ARNs here for notifications
  ok_actions    = []  # You can add SNS topic ARNs here for notifications

  tags = {
    Name        = "ss-monitoring-db-storage-alarm"
    Environment = "dev"
  }
} 