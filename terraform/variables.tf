data "aws_partition" "current" {}

variable "project_name" {
	description = "Project identifier used in IAM role and policy names."
	type        = string
	default     = "fire-sale"
}

variable "environment" {
	description = "Environment identifier (for example dev, staging, prod)."
	type        = string
	default     = "prod"
}

variable "step_function_state_machine_arn" {
	description = "State machine ARN started by EventBridge Scheduler."
	type        = string
}

variable "tracked_product_checker_lambda_arn" {
	description = "Lambda ARN for tracked product checker."
	type        = string
}

variable "scraper_overclockers_lambda_arn" {
	description = "Lambda ARN for Overclockers scraper."
	type        = string
}

variable "scraper_ebuyer_lambda_arn" {
	description = "Lambda ARN for Ebuyer scraper."
	type        = string
}

variable "scraper_scan_lambda_arn" {
	description = "Lambda ARN for Scan scraper."
	type        = string
}

variable "cleaning_lambda_arn" {
	description = "Lambda ARN for cleaning data."
	type        = string
}

variable "determine_notification_lambda_arn" {
	description = "Lambda ARN for generating notifications."
	type        = string
}

variable "rds_secret_arn" {
	description = "Secrets Manager secret ARN containing DB credentials."
	type        = string
}

variable "rds_kms_key_arn" {
	description = "Optional KMS key ARN if the DB secret uses a customer-managed key."
	type        = string
	default     = null
}

variable "tracked_product_checker_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for tracked product checker Lambda."
	type        = string
	default     = null
}

variable "cleaning_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for cleaning Lambda."
	type        = string
	default     = null
}

variable "determine_notification_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for determine notification Lambda."
	type        = string
	default     = null
}

variable "dashboard_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for Streamlit dashboard task."
	type        = string
	default     = null
}

variable "discord_bot_rds_db_user_arn" {
	description = "Optional RDS IAM DB user ARN for Discord bot task."
	type        = string
	default     = null
}

variable "ses_identity_arn" {
	description = "SES identity ARN used as sender identity."
	type        = string
}

variable "discord_alert_queue_arn" {
	description = "SQS queue ARN used to deliver alerts to the Discord bot."
	type        = string
}

variable "lambda_tracked_checker_log_group_arn" {
	description = "CloudWatch log group ARN for tracked product checker Lambda."
	type        = string
}

variable "lambda_scraper_overclockers_log_group_arn" {
	description = "CloudWatch log group ARN for Overclockers scraper Lambda."
	type        = string
}

variable "lambda_scraper_ebuyer_log_group_arn" {
	description = "CloudWatch log group ARN for Ebuyer scraper Lambda."
	type        = string
}

variable "lambda_scraper_scan_log_group_arn" {
	description = "CloudWatch log group ARN for Scan scraper Lambda."
	type        = string
}

variable "lambda_cleaning_log_group_arn" {
	description = "CloudWatch log group ARN for cleaning Lambda."
	type        = string
}

variable "lambda_determine_notification_log_group_arn" {
	description = "CloudWatch log group ARN for determine notification Lambda."
	type        = string
}
