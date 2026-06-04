output "rds_endpoint" {
  description = "RDS instance endpoint."
  value       = aws_db_instance.main.endpoint
}

output "rds_master_user_secret_arn" {
  description = "Secrets Manager ARN for the RDS master user password."
  value       = aws_db_instance.main.master_user_secret[0].secret_arn
}

output "lambda_ecr_repository_urls" {
  description = "Map of ECR repository URLs for all Lambda functions, keyed by function slug."
  value       = { for k, v in aws_ecr_repository.lambda : k => v.repository_url }
}

output "dashboard_ecr_repository_url" {
  description = "ECR repository URL for the Streamlit dashboard image."
  value       = aws_ecr_repository.dashboard.repository_url
}

output "discord_bot_ecr_repository_url" {
  description = "ECR repository URL for the Discord bot image."
  value       = aws_ecr_repository.discord_bot.repository_url
}

output "step_function_arn" {
  description = "ARN of the fire-sale Step Functions state machine."
  value       = aws_sfn_state_machine.main.arn
}

output "ecs_cluster_arn" {
  description = "ARN of the shared ECS cluster."
  value       = data.aws_ecs_cluster.main.arn
}

output "rds_connection_secret_arn" {
  description = "ARN of the RDS connection details secret."
  value       = aws_secretsmanager_secret.rds_connection.arn
}
