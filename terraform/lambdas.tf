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

# Tracked Product Checker Lambda

resource "aws_iam_role" "lambda_tracked_product_checker" {
	name               = "${var.project_name}-${var.environment}-lambda-tracked-product-checker"
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
			var.lambda_tracked_checker_log_group_arn,
			"${var.lambda_tracked_checker_log_group_arn}:*",
		]
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
	name   = "${var.project_name}-${var.environment}-lambda-tracked-product-checker"
	policy = data.aws_iam_policy_document.lambda_tracked_product_checker.json
}

resource "aws_iam_role_policy_attachment" "lambda_tracked_product_checker" {
	role       = aws_iam_role.lambda_tracked_product_checker.name
	policy_arn = aws_iam_policy.lambda_tracked_product_checker.arn
}

# Overclockers Scraper Lambda

resource "aws_iam_role" "lambda_scraper_overclockers" {
	name               = "${var.project_name}-${var.environment}-lambda-scraper-overclockers"
	assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_scraper_overclockers" {
	statement {
		sid    = "AllowLambdaLogging"
		effect = "Allow"

		actions = [
			"logs:CreateLogStream",
			"logs:PutLogEvents",
		]

		resources = [
			var.lambda_scraper_overclockers_log_group_arn,
			"${var.lambda_scraper_overclockers_log_group_arn}:*",
		]
	}
}

resource "aws_iam_policy" "lambda_scraper_overclockers" {
	name   = "${var.project_name}-${var.environment}-lambda-scraper-overclockers"
	policy = data.aws_iam_policy_document.lambda_scraper_overclockers.json
}

resource "aws_iam_role_policy_attachment" "lambda_scraper_overclockers" {
	role       = aws_iam_role.lambda_scraper_overclockers.name
	policy_arn = aws_iam_policy.lambda_scraper_overclockers.arn
}

# Ebuyer Scraper Lambda

resource "aws_iam_role" "lambda_scraper_ebuyer" {
	name               = "${var.project_name}-${var.environment}-lambda-scraper-ebuyer"
	assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_scraper_ebuyer" {
	statement {
		sid    = "AllowLambdaLogging"
		effect = "Allow"

		actions = [
			"logs:CreateLogStream",
			"logs:PutLogEvents",
		]

		resources = [
			var.lambda_scraper_ebuyer_log_group_arn,
			"${var.lambda_scraper_ebuyer_log_group_arn}:*",
		]
	}
}

resource "aws_iam_policy" "lambda_scraper_ebuyer" {
	name   = "${var.project_name}-${var.environment}-lambda-scraper-ebuyer"
	policy = data.aws_iam_policy_document.lambda_scraper_ebuyer.json
}

resource "aws_iam_role_policy_attachment" "lambda_scraper_ebuyer" {
	role       = aws_iam_role.lambda_scraper_ebuyer.name
	policy_arn = aws_iam_policy.lambda_scraper_ebuyer.arn
}

# Scan Scraper Lambda

resource "aws_iam_role" "lambda_scraper_scan" {
	name               = "${var.project_name}-${var.environment}-lambda-scraper-scan"
	assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_scraper_scan" {
	statement {
		sid    = "AllowLambdaLogging"
		effect = "Allow"

		actions = [
			"logs:CreateLogStream",
			"logs:PutLogEvents",
		]

		resources = [
			var.lambda_scraper_scan_log_group_arn,
			"${var.lambda_scraper_scan_log_group_arn}:*",
		]
	}
}

resource "aws_iam_policy" "lambda_scraper_scan" {
	name   = "${var.project_name}-${var.environment}-lambda-scraper-scan"
	policy = data.aws_iam_policy_document.lambda_scraper_scan.json
}

resource "aws_iam_role_policy_attachment" "lambda_scraper_scan" {
	role       = aws_iam_role.lambda_scraper_scan.name
	policy_arn = aws_iam_policy.lambda_scraper_scan.arn
}

# Cleaning Lambda

resource "aws_iam_role" "lambda_cleaning" {
	name               = "${var.project_name}-${var.environment}-lambda-cleaning"
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
			var.lambda_cleaning_log_group_arn,
			"${var.lambda_cleaning_log_group_arn}:*",
		]
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
	name   = "${var.project_name}-${var.environment}-lambda-cleaning"
	policy = data.aws_iam_policy_document.lambda_cleaning.json
}

resource "aws_iam_role_policy_attachment" "lambda_cleaning" {
	role       = aws_iam_role.lambda_cleaning.name
	policy_arn = aws_iam_policy.lambda_cleaning.arn
}

# Determine Notification Lambda

resource "aws_iam_role" "lambda_determine_notification" {
	name               = "${var.project_name}-${var.environment}-lambda-determine-notification"
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
			var.lambda_determine_notification_log_group_arn,
			"${var.lambda_determine_notification_log_group_arn}:*",
		]
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

		resources = [var.discord_alert_queue_arn]
	}
}

resource "aws_iam_policy" "lambda_determine_notification" {
	name   = "${var.project_name}-${var.environment}-lambda-determine-notification"
	policy = data.aws_iam_policy_document.lambda_determine_notification.json
}

resource "aws_iam_role_policy_attachment" "lambda_determine_notification" {
	role       = aws_iam_role.lambda_determine_notification.name
	policy_arn = aws_iam_policy.lambda_determine_notification.arn
}
