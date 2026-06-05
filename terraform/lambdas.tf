data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "AllowLambdaServiceToAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ── Lambda VPC Configuration ──────────────────────────────────────────────────
# Lambdas use the existing c23 VPC and public subnets (defined in rds.tf)
# for stable outbound IP. They have a dedicated security group for egress.

resource "aws_security_group" "lambda" {
  name        = "${var.cohort}-${var.project_name}-${var.environment}-lambda"
  description = "Allow Lambda functions outbound internet access for web scraping."
  vpc_id      = data.aws_vpc.main.id
}

resource "aws_vpc_security_group_egress_rule" "lambda_https" {
  security_group_id = aws_security_group.lambda.id
  description       = "HTTPS outbound to the internet for web scraping"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "lambda_http" {
  security_group_id = aws_security_group.lambda.id
  description       = "HTTP outbound to the internet for web scraping"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "lambda_dns_udp" {
  security_group_id = aws_security_group.lambda.id
  description       = "DNS (UDP) outbound to resolve domain names"
  from_port         = 53
  to_port           = 53
  ip_protocol       = "udp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "lambda_dns_tcp" {
  security_group_id = aws_security_group.lambda.id
  description       = "DNS (TCP) outbound to resolve domain names"
  from_port         = 53
  to_port           = 53
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

# Tracked Product Checker Lambda

resource "aws_iam_role" "lambda_tracked_product_checker" {
  name               = "${var.cohort}-${var.project_name}-${var.environment}-lambda-tracked-product-checker"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_tracked_product_checker" {
  statement {
    sid    = "AllowLambdaLogging"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.lambda_tracked_product_checker.arn,
      "${aws_cloudwatch_log_group.lambda_tracked_product_checker.arn}:*",
    ]
  }

  statement {
    sid    = "AllowReadDbSecret"
    effect = "Allow"

    actions = ["secretsmanager:GetSecretValue"]

    resources = [
      aws_db_instance.main.master_user_secret[0].secret_arn,
      aws_secretsmanager_secret.rds_connection.arn
    ]
  }

  statement {
    sid    = "AllowCreateNetworkInterface"
    effect = "Allow"

    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
    ]

    resources = ["*"]
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
    for_each = var.tracked_product_checker_rds_db_user_arn == null ? [] : [var.tracked_product_checker_rds_db_user_arn]

    content {
      sid    = "AllowConnectToRdsWithIamAuth"
      effect = "Allow"

      actions = ["rds-db:connect"]

      resources = [statement.value]
    }
  }
}

resource "aws_iam_policy" "lambda_tracked_product_checker" {
  name   = "${var.cohort}-${var.project_name}-${var.environment}-lambda-tracked-product-checker"
  policy = data.aws_iam_policy_document.lambda_tracked_product_checker.json
}

resource "aws_iam_role_policy_attachment" "lambda_tracked_product_checker" {
  role       = aws_iam_role.lambda_tracked_product_checker.name
  policy_arn = aws_iam_policy.lambda_tracked_product_checker.arn
}

# Scraper Lambdas — one per website, driven by var.scraper_names.
# Add a new slug to that variable and Terraform will provision everything below.

resource "aws_cloudwatch_log_group" "lambda_scraper" {
  for_each          = toset(var.scraper_names)
  name              = "/aws/lambda/${var.cohort}-${var.project_name}-${var.environment}-scraper-${each.key}"
  retention_in_days = 14
}

resource "aws_iam_role" "lambda_scraper" {
  for_each           = toset(var.scraper_names)
  name               = "${var.cohort}-${var.project_name}-${var.environment}-lambda-scraper-${each.key}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_scraper" {
  for_each = toset(var.scraper_names)

  statement {
    sid    = "AllowLambdaLogging"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.lambda_scraper[each.key].arn,
      "${aws_cloudwatch_log_group.lambda_scraper[each.key].arn}:*",
    ]
  }

  statement {
    sid    = "AllowCreateNetworkInterface"
    effect = "Allow"

    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_scraper" {
  for_each = toset(var.scraper_names)
  name     = "${var.cohort}-${var.project_name}-${var.environment}-lambda-scraper-${each.key}"
  policy   = data.aws_iam_policy_document.lambda_scraper[each.key].json
}

resource "aws_iam_role_policy_attachment" "lambda_scraper" {
  for_each   = toset(var.scraper_names)
  role       = aws_iam_role.lambda_scraper[each.key].name
  policy_arn = aws_iam_policy.lambda_scraper[each.key].arn
}

# Cleaning Lambda

resource "aws_iam_role" "lambda_cleaning" {
  name               = "${var.cohort}-${var.project_name}-${var.environment}-lambda-cleaning"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_cleaning" {
  statement {
    sid    = "AllowLambdaLogging"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.lambda_cleaning.arn,
      "${aws_cloudwatch_log_group.lambda_cleaning.arn}:*",
    ]
  }

  statement {
    sid    = "AllowCreateNetworkInterface"
    effect = "Allow"

    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "AllowReadDbSecret"
    effect = "Allow"

    actions = ["secretsmanager:GetSecretValue"]

    resources = [
      aws_db_instance.main.master_user_secret[0].secret_arn,
      aws_secretsmanager_secret.rds_connection.arn,
    ]
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
    for_each = var.cleaning_rds_db_user_arn == null ? [] : [var.cleaning_rds_db_user_arn]

    content {
      sid    = "AllowConnectToRdsWithIamAuth"
      effect = "Allow"

      actions = ["rds-db:connect"]

      resources = [statement.value]
    }
  }
}

resource "aws_iam_policy" "lambda_cleaning" {
  name   = "${var.cohort}-${var.project_name}-${var.environment}-lambda-cleaning"
  policy = data.aws_iam_policy_document.lambda_cleaning.json
}

resource "aws_iam_role_policy_attachment" "lambda_cleaning" {
  role       = aws_iam_role.lambda_cleaning.name
  policy_arn = aws_iam_policy.lambda_cleaning.arn
}

# Determine Notification Lambda

resource "aws_iam_role" "lambda_determine_notification" {
  name               = "${var.cohort}-${var.project_name}-${var.environment}-lambda-determine-notification"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_determine_notification" {
  statement {
    sid    = "AllowLambdaLogging"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.lambda_determine_notification.arn,
      "${aws_cloudwatch_log_group.lambda_determine_notification.arn}:*",
    ]
  }

  statement {
    sid    = "AllowCreateNetworkInterface"
    effect = "Allow"

    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "AllowReadDbSecret"
    effect = "Allow"

    actions = ["secretsmanager:GetSecretValue"]

    resources = [
      aws_db_instance.main.master_user_secret[0].secret_arn,
      aws_secretsmanager_secret.rds_connection.arn,
    ]
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
    for_each = var.determine_notification_rds_db_user_arn == null ? [] : [var.determine_notification_rds_db_user_arn]

    content {
      sid    = "AllowConnectToRdsWithIamAuth"
      effect = "Allow"

      actions = ["rds-db:connect"]

      resources = [statement.value]
    }
  }

  statement {
    sid    = "AllowSendingEmailFromApprovedIdentity"
    effect = "Allow"

    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail",
    ]

    resources = [var.ses_identity_arn]
  }

  statement {
    sid    = "AllowEnqueueDiscordAlerts"
    effect = "Allow"

    actions = ["sqs:SendMessage"]

    resources = [aws_sqs_queue.discord_notifications.arn]
  }
}

resource "aws_iam_policy" "lambda_determine_notification" {
  name   = "${var.cohort}-${var.project_name}-${var.environment}-lambda-determine-notification"
  policy = data.aws_iam_policy_document.lambda_determine_notification.json
}

resource "aws_iam_role_policy_attachment" "lambda_determine_notification" {
  role       = aws_iam_role.lambda_determine_notification.name
  policy_arn = aws_iam_policy.lambda_determine_notification.arn
}

# ── CloudWatch Log Groups ─────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "lambda_tracked_product_checker" {
  name              = "/aws/lambda/${var.cohort}-${var.project_name}-${var.environment}-tracked-product-checker"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "lambda_cleaning" {
  name              = "/aws/lambda/${var.cohort}-${var.project_name}-${var.environment}-cleaning"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "lambda_determine_notification" {
  name              = "/aws/lambda/${var.cohort}-${var.project_name}-${var.environment}-determine-notification"
  retention_in_days = 14
}

# ── Lambda Functions ──────────────────────────────────────────────────────────
# Images must be pushed to the ECR repositories before these resources can be
# applied. Run `terraform apply -target=aws_ecr_repository.lambda` first, then
# build and push the images, then apply the rest.

resource "aws_lambda_function" "scraper" {
  for_each = toset(var.scraper_names)

  function_name = "${var.cohort}-${var.project_name}-${var.environment}-scraper-${each.key}"
  role          = aws_iam_role.lambda_scraper[each.key].arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda["scraper-${each.key}"].repository_url}:${var.image_tag}"
  timeout       = 300
  memory_size   = 512

  vpc_config {
    subnet_ids          = data.aws_subnets.public.ids
    security_group_ids  = [aws_security_group.lambda.id]
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_scraper[each.key].name
  }

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      WEBSITE_NAME = each.key
    }
  }
}

resource "aws_lambda_function" "tracked_product_checker" {
  function_name = "${var.cohort}-${var.project_name}-${var.environment}-tracked-product-checker"
  role          = aws_iam_role.lambda_tracked_product_checker.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda["tracked-product-checker"].repository_url}:${var.image_tag}"
  timeout       = 180
  memory_size   = 256

  vpc_config {
    subnet_ids          = data.aws_subnets.public.ids
    security_group_ids  = [aws_security_group.lambda.id]
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_tracked_product_checker.name
  }

  environment {
    variables = {
      ENVIRONMENT   = var.environment
      DB_SECRET_ARN = aws_secretsmanager_secret.rds_connection.arn
    }
  }
}

resource "aws_lambda_function" "cleaning" {
  function_name = "${var.cohort}-${var.project_name}-${var.environment}-lambda-cleaning"
  role          = aws_iam_role.lambda_cleaning.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda["cleaning"].repository_url}:${var.image_tag}"
  timeout       = 180
  memory_size   = 256

  vpc_config {
    subnet_ids          = data.aws_subnets.public.ids
    security_group_ids  = [aws_security_group.lambda.id]
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_cleaning.name
  }

  environment {
    variables = {
      ENVIRONMENT   = var.environment
      DB_SECRET_ARN = aws_secretsmanager_secret.rds_connection.arn
    }
  }
}

resource "aws_lambda_function" "determine_notification" {
  function_name = "${var.cohort}-${var.project_name}-${var.environment}-lambda-determine-notification"
  role          = aws_iam_role.lambda_determine_notification.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda["determine-notification"].repository_url}:${var.image_tag}"
  timeout       = 60
  memory_size   = 128

  vpc_config {
    subnet_ids          = data.aws_subnets.public.ids
    security_group_ids  = [aws_security_group.lambda.id]
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_determine_notification.name
  }

  environment {
    variables = {
      ENVIRONMENT   = var.environment
      DB_SECRET_ARN = aws_secretsmanager_secret.rds_connection.arn
    }
  }
}

