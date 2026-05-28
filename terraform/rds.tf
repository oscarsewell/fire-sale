# Data source for c23 VPC
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["c23-VPC"]
  }
}

# Data sources for c23 public subnets
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["c23-public-subnet-*"]
  }
}

# Security group for RDS
resource "aws_security_group" "rds" {
  name        = "c23-fire-sale-rds-sg"
  description = "Security group for Postgres RDS"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # restrict to personal IP/VPC in production so it can't be brute forced
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "c23-fire-sale-rds-sg"
  }
}

# DB subnet group
resource "aws_db_subnet_group" "rds" {
  name       = "c23-fire-sale-rds-subnet-group"
  subnet_ids = data.aws_subnets.public.ids

  tags = {
    Name = "c23-fire-sale-rds-subnet-group"
  }
}

# RDS Postgres instance
resource "aws_db_instance" "postgres" {
  identifier     = "c23-fire-sale-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"

  db_name  = "firesale"
  username = "postgres"
  password = random_password.db_password.result

  allocated_storage = 20
  storage_type      = "gp3"

  publicly_accessible    = true
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot = true

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "c23-fire-sale-postgres"
  }

  depends_on = [aws_db_subnet_group.rds]
}

# Random password for database
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%^&*()-_=+[]{}:;,.?"
}

# Store password in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "c23-fire-sale/rds/password"

  tags = {
    Name = "c23-fire-sale-rds-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = "postgres"
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = 5432
    dbname   = "firesale"
  })
}

# IAM role for ECS and Lambda to access RDS
resource "aws_iam_role" "rds_access" {
  name = "c23-fire-sale-rds-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ecs-tasks.amazonaws.com", "lambda.amazonaws.com"]
        }
      }
    ]
  })
}

# Outputs
output "rds_endpoint" {
  description = "RDS endpoint for remote connection"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = false
}

output "rds_address" {
  description = "RDS address"
  value       = aws_db_instance.postgres.address
  sensitive   = false
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.postgres.port
  sensitive   = false
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
  sensitive   = false
}

output "db_secret_arn" {
  description = "ARN of the database password secret"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = false
}
