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
	name               = "${var.project_name}-${var.environment}-step-functions-execution"
	assume_role_policy = data.aws_iam_policy_document.step_functions_assume_role.json
}

data "aws_iam_policy_document" "step_functions_invoke_lambdas" {
	statement {
		sid    = "AllowInvokingWorkflowLambdas"
		effect = "Allow"

		actions = ["lambda:InvokeFunction"]

		resources = [
			var.tracked_product_checker_lambda_arn,
			var.scraper_overclockers_lambda_arn,
			var.scraper_ebuyer_lambda_arn,
			var.scraper_scan_lambda_arn,
			var.cleaning_lambda_arn,
			var.determine_notification_lambda_arn,
		]
	}
}

resource "aws_iam_policy" "step_functions_invoke_lambdas" {
	name   = "${var.project_name}-${var.environment}-step-functions-invoke-lambdas"
	policy = data.aws_iam_policy_document.step_functions_invoke_lambdas.json
}

resource "aws_iam_role_policy_attachment" "step_functions_invoke_lambdas" {
	role       = aws_iam_role.step_functions_execution.name
	policy_arn = aws_iam_policy.step_functions_invoke_lambdas.arn
}
