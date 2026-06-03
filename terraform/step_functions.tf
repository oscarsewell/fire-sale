data "aws_iam_policy_document" "step_functions_assume_role" {
	statement {
		sid     = "AllowStepFunctionsServiceToAssumeRole"
		effect  = "Allow"
		actions = ["sts:AssumeRole"]

		principals {
			type        = "Service"
			identifiers = ["states.amazonaws.com"]
		}
	}
}

resource "aws_iam_role" "step_functions_execution" {
	name               = "${var.cohort}-${var.project_name}-${var.environment}-step-functions-execution"
	assume_role_policy = data.aws_iam_policy_document.step_functions_assume_role.json
}

data "aws_iam_policy_document" "step_functions_invoke_lambdas" {
	statement {
		sid    = "AllowInvokingWorkflowLambdas"
		effect = "Allow"

		actions = ["lambda:InvokeFunction"]

		resources = concat(
			[
				aws_lambda_function.tracked_product_checker.arn,
				aws_lambda_function.cleaning.arn,
				aws_lambda_function.determine_notification.arn,
			],
			[for name in var.scraper_names : aws_lambda_function.scraper[name].arn],
		)
	}
}

resource "aws_iam_policy" "step_functions_invoke_lambdas" {
	name   = "${var.cohort}-${var.project_name}-${var.environment}-step-functions-invoke-lambdas"
	policy = data.aws_iam_policy_document.step_functions_invoke_lambdas.json
}

resource "aws_iam_role_policy_attachment" "step_functions_invoke_lambdas" {
	role       = aws_iam_role.step_functions_execution.name
	policy_arn = aws_iam_policy.step_functions_invoke_lambdas.arn
}

# ── State Machine ─────────────────────────────────────────────────────────────
# Workflow: tracked product checker → parallel scraper fan-out → clean → notify.
# Scraper branches are generated dynamically from var.scraper_names so adding a
# new retailer only requires updating that variable.

resource "aws_sfn_state_machine" "main" {
	name     = "${var.cohort}-${var.project_name}-${var.environment}-step-functions"
	role_arn = aws_iam_role.step_functions_execution.arn
	type     = "STANDARD"

	definition = jsonencode({
		Comment = "fire-sale: check tracked products, scrape retailers, clean data, notify users."
		StartAt = "GetTrackedProducts"
		States = {
			GetTrackedProducts = {
				Type     = "Task"
				Resource = "arn:aws:states:::lambda:invoke"
				Parameters = {
					FunctionName = aws_lambda_function.tracked_product_checker.arn
					"Payload.$"  = "$"
				}
				ResultSelector = { "urls.$" = "$.Payload.urls" }
				ResultPath     = "$.tracked"
				Next           = "ScrapeWebsites"
			}

			ScrapeWebsites = {
				Type = "Parallel"
				Branches = [
					for name in var.scraper_names : {
						StartAt = "Scrape-${name}"
						States = {
							for k in ["Scrape-${name}"] : k => {
								Type     = "Task"
								Resource = "arn:aws:states:::lambda:invoke"
								Parameters = {
									FunctionName = aws_lambda_function.scraper[name].arn
									"Payload.$"  = "$.tracked"
								}
								End = true
							}
						}
					}
				]
				ResultPath = "$.scraped"
				Next       = "CleanData"
			}

			CleanData = {
				Type     = "Task"
				Resource = "arn:aws:states:::lambda:invoke"
				Parameters = {
					FunctionName = aws_lambda_function.cleaning.arn
					"Payload.$"  = "$.scraped"
				}
				ResultSelector = { "result.$" = "$.Payload" }
				ResultPath     = "$.cleaned"
				Next           = "DetermineNotification"
			}

			DetermineNotification = {
				Type     = "Task"
				Resource = "arn:aws:states:::lambda:invoke"
				Parameters = {
					FunctionName = aws_lambda_function.determine_notification.arn
					"Payload.$"  = "$.cleaned"
				}
				End = true
			}
		}
	})
}

