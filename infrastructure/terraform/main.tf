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
# resource "aws_key_pair" "main" {
#   key_name   = "ss-monitoring-key"  
#   public_key = file("~/.ssh/id_rsa.pub") # Change this path to your public key
# 
#   tags = {
#     Name        = "ss-monitoring-key"
#     Environment = "dev"
#   }
# }

# EC2 Instance (Free Tier)
resource "aws_instance" "app" {
  ami                    = "ami-0c02fb55956c7d316" # Amazon Linux 2023 in us-east-1 - update if needed for your region
  instance_type          = "t2.micro" # Free tier eligible - 750 hours/month
  # key_name               = aws_key_pair.main.key_name # Commented out - no SSH access for now
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]

  # User data script to install basic dependencies
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y python3 python3-pip git
    
    # Create app directory
    mkdir -p /opt/solar-monitoring
    chown ec2-user:ec2-user /opt/solar-monitoring
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

# RDS Instance (Free Tier) - Publicly accessible for pgAdmin
resource "aws_db_instance" "postgres" {
  identifier                = "ss-monitoring-db"
  engine                    = "postgres"
  engine_version            = "16.8"
  instance_class            = "db.t3.micro" # Free tier eligible - updated from deprecated db.t2.micro
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

  skip_final_snapshot = true
  deletion_protection = false

  backup_retention_period = 0 # Disable backups for free tier
  
  tags = {
    Name        = "ss-monitoring-db"
    Environment = "dev"
  }
} 