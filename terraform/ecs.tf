data "aws_iam_policy_document" "ecs_tasks_assume_role" {
	statement {
		sid     = "AllowECSTasksServiceToAssumeRole"
		effect  = "Allow"
		actions = ["sts:AssumeRole"]

		principals {
			type        = "Service"
			identifiers = ["ecs-tasks.amazonaws.com"]
		}
	}
}

# ECS Task Execution Role (required for ECS agent to pull images and logs)

resource "aws_iam_role" "ecs_task_execution" {
	name               = "${var.project_name}-${var.environment}-ecs-task-execution"
	assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
	role       = aws_iam_role.ecs_task_execution.name
	policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Dashboard Task Role

resource "aws_iam_role" "ecs_dashboard_task" {
	name               = "${var.project_name}-${var.environment}-ecs-dashboard-task"
	assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

data "aws_iam_policy_document" "ecs_dashboard_task" {
	statement {
		sid    = "AllowReadDbSecret"
		effect = "Allow"

		actions = ["secretsmanager:GetSecretValue"]

		resources = [var.rds_secret_arn]
	}

	dynamic "statement" {
		for_each = var.rds_kms_key_arn == null ? [] : [var.rds_kms_key_arn]

		content {
			sid    = "AllowDecryptDbSecretKey"
			effect = "Allow"

			actions = ["kms:Decrypt"]

			resources = [statement.value]
		}
	}

	dynamic "statement" {
		for_each = var.dashboard_rds_db_user_arn == null ? [] : [var.dashboard_rds_db_user_arn]

		content {
			sid    = "AllowConnectToRdsWithIamAuth"
			effect = "Allow"

			actions = ["rds-db:connect"]

			resources = [statement.value]
		}
	}
}

resource "aws_iam_policy" "ecs_dashboard_task" {
	name   = "${var.project_name}-${var.environment}-ecs-dashboard-task"
	policy = data.aws_iam_policy_document.ecs_dashboard_task.json
}

resource "aws_iam_role_policy_attachment" "ecs_dashboard_task" {
	role       = aws_iam_role.ecs_dashboard_task.name
	policy_arn = aws_iam_policy.ecs_dashboard_task.arn
}

# Discord Bot Task Role

resource "aws_iam_role" "ecs_discord_bot_task" {
	name               = "${var.project_name}-${var.environment}-ecs-discord-bot-task"
	assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

data "aws_iam_policy_document" "ecs_discord_bot_task" {
	statement {
		sid    = "AllowConsumeDiscordAlertQueue"
		effect = "Allow"

		actions = [
			"sqs:ReceiveMessage",
			"sqs:DeleteMessage",
			"sqs:GetQueueAttributes",
			"sqs:ChangeMessageVisibility",
		]

		resources = [var.discord_alert_queue_arn]
	}

	statement {
		sid    = "AllowReadDbSecret"
		effect = "Allow"

		actions = ["secretsmanager:GetSecretValue"]

		resources = [var.rds_secret_arn]
	}

	dynamic "statement" {
		for_each = var.rds_kms_key_arn == null ? [] : [var.rds_kms_key_arn]

		content {
			sid    = "AllowDecryptDbSecretKey"
			effect = "Allow"

			actions = ["kms:Decrypt"]

			resources = [statement.value]
		}
	}

	dynamic "statement" {
		for_each = var.discord_bot_rds_db_user_arn == null ? [] : [var.discord_bot_rds_db_user_arn]

		content {
			sid    = "AllowConnectToRdsWithIamAuth"
			effect = "Allow"

			actions = ["rds-db:connect"]

			resources = [statement.value]
		}
	}
}

resource "aws_iam_policy" "ecs_discord_bot_task" {
	name   = "${var.project_name}-${var.environment}-ecs-discord-bot-task"
	policy = data.aws_iam_policy_document.ecs_discord_bot_task.json
}

resource "aws_iam_role_policy_attachment" "ecs_discord_bot_task" {
	role       = aws_iam_role.ecs_discord_bot_task.name
	policy_arn = aws_iam_policy.ecs_discord_bot_task.arn
}
