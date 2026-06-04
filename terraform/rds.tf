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

# RDS security group — ingress rules reference the Lambda VPC SG (lambdas.tf)
# and ECS SG (ecs.tf); Terraform resolves cross-file dependencies automatically.

resource "aws_security_group" "rds" {
	name        = "${var.cohort}-${var.project_name}-${var.environment}-rds"
	description = "Allow inbound PostgreSQL from VPC-attached Lambda functions and ECS tasks."
	vpc_id      = data.aws_vpc.main.id
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
	security_group_id            = aws_security_group.rds.id
	referenced_security_group_id = aws_security_group.ecs.id
	from_port                    = 5432
	to_port                      = 5432
	ip_protocol                  = "tcp"
	description                  = "PostgreSQL from ECS tasks."
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_internet" {
	security_group_id = aws_security_group.rds.id
	cidr_ipv4         = "0.0.0.0/0"
	from_port         = 5432
	to_port           = 5432
	ip_protocol       = "tcp"
	description       = "PostgreSQL from Lambda functions (no VPC). Restrict to known CIDRs in production."
}

resource "aws_db_subnet_group" "main" {
	name       = "${var.cohort}-${var.project_name}-${var.environment}-rds"
	subnet_ids = data.aws_subnets.public.ids
}

resource "aws_db_instance" "main" {
	identifier = "${var.cohort}-${var.project_name}-${var.environment}-rds"

	engine         = "postgres"
	engine_version = "16"
	instance_class = var.rds_instance_class

	db_name  = var.rds_db_name
	username = var.rds_master_username

	# Secrets Manager manages the master password; use the output
	# rds_master_user_secret_arn as var.rds_secret_arn in other modules if needed.
	manage_master_user_password = true

	allocated_storage      = 20
	db_subnet_group_name   = aws_db_subnet_group.main.name
	vpc_security_group_ids = [aws_security_group.rds.id]

	iam_database_authentication_enabled = true
	storage_encrypted                   = true
	publicly_accessible                 = true

	# Flip both to true before going to production.
	deletion_protection = false
	skip_final_snapshot = true
}

# Custom secret containing full DB connection details
resource "aws_secretsmanager_secret" "rds_connection" {
	name                    = "${var.cohort}-${var.project_name}-${var.environment}-rds-connection"
	description             = "RDS database connection details for ${var.project_name}"
	recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "rds_connection" {
	secret_id = aws_secretsmanager_secret.rds_connection.id
	secret_string = jsonencode({
		host               = aws_db_instance.main.address
		port               = aws_db_instance.main.port
		dbname             = aws_db_instance.main.db_name
		username           = aws_db_instance.main.username
		password_secret_arn = aws_db_instance.main.master_user_secret[0].secret_arn
	})
}
