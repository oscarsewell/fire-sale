data "aws_partition" "current" {}

# ── Identity ──────────────────────────────────────────────────────────────────

variable "project_name" {
	description = "Project identifier used in resource names."
	type        = string
	default     = "fire-sale"
}

variable "environment" {
	description = "Environment identifier (e.g. dev, staging, prod)."
	type        = string
	default     = "prod"
}

# ── Networking ────────────────────────────────────────────────────────────────

variable "aws_region" {
	description = "AWS region for the provider and CloudWatch log configuration."
	type        = string
	default     = "eu-west-2"
}

# ── Scraper configuration ─────────────────────────────────────────────────────

variable "scraper_names" {
	description = "List of website slugs to scrape. Each entry gets its own Lambda function and ECR repository. Add a new slug here to support a new retailer."
	type        = list(string)
	default     = ["overclockers", "ebuyer", "awd-it"]
}

# ── Container images ──────────────────────────────────────────────────────────

variable "image_tag" {
	description = "Docker image tag to deploy for all Lambda functions and ECS tasks."
	type        = string
	default     = "latest"
}

# ── RDS ───────────────────────────────────────────────────────────────────────

variable "rds_instance_class" {
	description = "RDS instance class."
	type        = string
	default     = "db.t4g.micro"
}

variable "rds_db_name" {
	description = "Name of the initial database created on the RDS instance."
	type        = string
	default     = "firesale"
}

variable "rds_master_username" {
	description = "Master username for the RDS instance."
	type        = string
	default     = "postgres"
}

variable "rds_kms_key_arn" {
	description = "Optional KMS key ARN if the RDS Secrets Manager secret uses a customer-managed key."
	type        = string
	default     = null
}

# ── RDS IAM auth user ARNs (optional) ────────────────────────────────────────

variable "tracked_product_checker_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for the tracked product checker Lambda."
	type        = string
	default     = null
}

variable "cleaning_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for the cleaning Lambda."
	type        = string
	default     = null
}

variable "determine_notification_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for the determine notification Lambda."
	type        = string
	default     = null
}

variable "dashboard_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for the Streamlit dashboard ECS task."
	type        = string
	default     = null
}

variable "discord_bot_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for the Discord bot ECS task."
	type        = string
	default     = null
}

# ── External service ARNs ─────────────────────────────────────────────────────

variable "ses_identity_arn" {
	description = "SES verified identity ARN used as the email sender."
	type        = string
}

variable "discord_alert_queue_arn" {
	description = "SQS queue ARN used to deliver price-alert messages to the Discord bot."
	type        = string
}
