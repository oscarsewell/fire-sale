# ── ECS Cluster ───────────────────────────────────────────────────────────────
# Referencing a pre-existing shared cluster rather than managing it here.

data "aws_ecs_cluster" "main" {
  cluster_name = "c23-ecs-cluster"
}

# ── Security Group for ECS Tasks ─────────────────────────────────────────────

resource "aws_security_group" "ecs" {
  name        = "${var.cohort}-${var.project_name}-${var.environment}-ecs"
  description = "Security group for ECS Fargate tasks (dashboard and Discord bot)."
  vpc_id      = data.aws_vpc.main.id
}

resource "aws_vpc_security_group_egress_rule" "ecs_all_outbound" {
  security_group_id = aws_security_group.ecs.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic."
}

# Streamlit listens on 8501. For production, restrict this to an ALB security
# group rather than opening it to the public internet directly.
resource "aws_vpc_security_group_ingress_rule" "ecs_dashboard_streamlit" {
  security_group_id = aws_security_group.ecs.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8501
  to_port           = 8501
  ip_protocol       = "tcp"
  description       = "Streamlit dashboard inbound."
}

# ── CloudWatch Log Groups for ECS Tasks ───────────────────────────────────────

resource "aws_cloudwatch_log_group" "ecs_dashboard" {
  name              = "/ecs/${var.cohort}-${var.project_name}-${var.environment}-dashboard"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ecs_discord_bot" {
  name              = "/ecs/${var.cohort}-${var.project_name}-${var.environment}-discord-bot"
  retention_in_days = 14
}

# ── IAM ───────────────────────────────────────────────────────────────────────

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
  name               = "${var.cohort}-${var.project_name}-${var.environment}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Dashboard Task Role

resource "aws_iam_role" "ecs_dashboard_task" {
  name               = "${var.cohort}-${var.project_name}-${var.environment}-ecs-dashboard-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

data "aws_iam_policy_document" "ecs_dashboard_task" {
  statement {
    sid    = "AllowReadDbSecret"
    effect = "Allow"

    actions = ["secretsmanager:GetSecretValue"]

    resources = [aws_db_instance.main.master_user_secret[0].secret_arn]
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
  name   = "${var.cohort}-${var.project_name}-${var.environment}-ecs-dashboard-task"
  policy = data.aws_iam_policy_document.ecs_dashboard_task.json
}

resource "aws_iam_role_policy_attachment" "ecs_dashboard_task" {
  role       = aws_iam_role.ecs_dashboard_task.name
  policy_arn = aws_iam_policy.ecs_dashboard_task.arn
}

# Discord Bot Task Role

resource "aws_iam_role" "ecs_discord_bot_task" {
  name               = "${var.cohort}-${var.project_name}-${var.environment}-ecs-discord-bot-task"
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

    resources = [aws_sqs_queue.discord_notifications.arn]
  }

  statement {
    sid    = "AllowReadDbSecret"
    effect = "Allow"

    actions = ["secretsmanager:GetSecretValue"]

    resources = [aws_db_instance.main.master_user_secret[0].secret_arn]
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
  name   = "${var.cohort}-${var.project_name}-${var.environment}-ecs-discord-bot-task"
  policy = data.aws_iam_policy_document.ecs_discord_bot_task.json
}

resource "aws_iam_role_policy_attachment" "ecs_discord_bot_task" {
  role       = aws_iam_role.ecs_discord_bot_task.name
  policy_arn = aws_iam_policy.ecs_discord_bot_task.arn
}


# ── ECS Task Definitions ──────────────────────────────────────────────────────

resource "aws_ecs_task_definition" "dashboard" {
  family                   = "${var.cohort}-${var.project_name}-${var.environment}-dashboard"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_dashboard_task.arn

  container_definitions = jsonencode([{
    name      = "dashboard"
    image     = "${aws_ecr_repository.dashboard.repository_url}:${var.image_tag}"
    essential = true

    portMappings = [{
      containerPort = 8501
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs_dashboard.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "dashboard"
      }
    }

    environment = [
      { name = "ENVIRONMENT", value = var.environment }
    ]
  }])
}

resource "aws_ecs_task_definition" "discord_bot" {
  family                   = "${var.cohort}-${var.project_name}-${var.environment}-discord-bot"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_discord_bot_task.arn

  container_definitions = jsonencode([{
    name      = "discord-bot"
    image     = "${aws_ecr_repository.discord_bot.repository_url}:${var.image_tag}"
    essential = true

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs_discord_bot.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "discord-bot"
      }
    }

    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "DISCORD_NOTIFICATION_QUEUE_URL", value = aws_sqs_queue.discord_notifications.url }
    ]
  }])
}

# ── ECS Services ──────────────────────────────────────────────────────────────

resource "aws_ecs_service" "dashboard" {
  name            = "${var.cohort}-${var.project_name}-${var.environment}-dashboard"
  cluster         = data.aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.dashboard.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  # Prevent Terraform from rolling back task definition updates made by CI/CD.
  lifecycle {
    ignore_changes = [task_definition]
  }
}

resource "aws_ecs_service" "discord_bot" {
  name            = "${var.cohort}-${var.project_name}-${var.environment}-discord-bot"
  cluster         = data.aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.discord_bot.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}