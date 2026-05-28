locals {
	# Scraper ECR names are derived from var.scraper_names so that adding a new
	# website scraper to the list automatically provisions its ECR repository.
	scraper_ecr_names = toset([for s in var.scraper_names : "scraper-${s}"])

	fixed_lambda_ecr_names = toset([
		"tracked-product-checker",
		"cleaning",
		"determine-notification",
	])

	all_lambda_ecr_names = setunion(local.fixed_lambda_ecr_names, local.scraper_ecr_names)
}

# ── Lambda ECR Repositories ───────────────────────────────────────────────────

resource "aws_ecr_repository" "lambda" {
	for_each = local.all_lambda_ecr_names

	name                 = "${var.project_name}-${var.environment}-lambda-${each.key}"
	image_tag_mutability = "MUTABLE"

	image_scanning_configuration {
		scan_on_push = true
	}
}

resource "aws_ecr_lifecycle_policy" "lambda" {
	for_each   = local.all_lambda_ecr_names
	repository = aws_ecr_repository.lambda[each.key].name

	policy = jsonencode({
		rules = [{
			rulePriority = 1
			description  = "Keep last 5 images."
			selection = {
				tagStatus   = "any"
				countType   = "imageCountMoreThan"
				countNumber = 5
			}
			action = { type = "expire" }
		}]
	})
}

# Allow the Lambda service to pull images from each Lambda ECR repository.
# This is required for Lambda container image functions to start.

resource "aws_ecr_repository_policy" "lambda" {
	for_each   = local.all_lambda_ecr_names
	repository = aws_ecr_repository.lambda[each.key].name

	policy = jsonencode({
		Version = "2012-10-17"
		Statement = [{
			Sid    = "AllowLambdaServiceImageRetrieval"
			Effect = "Allow"
			Principal = {
				Service = "lambda.amazonaws.com"
			}
			Action = [
				"ecr:BatchGetImage",
				"ecr:GetDownloadUrlForLayer",
			]
		}]
	})
}

# ── Dashboard ECR Repository ──────────────────────────────────────────────────

resource "aws_ecr_repository" "dashboard" {
	name                 = "${var.project_name}-${var.environment}-dashboard"
	image_tag_mutability = "MUTABLE"

	image_scanning_configuration {
		scan_on_push = true
	}
}

resource "aws_ecr_lifecycle_policy" "dashboard" {
	repository = aws_ecr_repository.dashboard.name

	policy = jsonencode({
		rules = [{
			rulePriority = 1
			description  = "Keep last 5 images."
			selection = {
				tagStatus   = "any"
				countType   = "imageCountMoreThan"
				countNumber = 5
			}
			action = { type = "expire" }
		}]
	})
}

# ── Discord Bot ECR Repository ────────────────────────────────────────────────

resource "aws_ecr_repository" "discord_bot" {
	name                 = "${var.project_name}-${var.environment}-discord-bot"
	image_tag_mutability = "MUTABLE"

	image_scanning_configuration {
		scan_on_push = true
	}
}

resource "aws_ecr_lifecycle_policy" "discord_bot" {
	repository = aws_ecr_repository.discord_bot.name

	policy = jsonencode({
		rules = [{
			rulePriority = 1
			description  = "Keep last 5 images."
			selection = {
				tagStatus   = "any"
				countType   = "imageCountMoreThan"
				countNumber = 5
			}
			action = { type = "expire" }
		}]
	})
}
