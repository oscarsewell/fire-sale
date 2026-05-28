data "aws_iam_policy_document" "scheduler_assume_role" {
	statement {
		sid     = "AllowSchedulerServiceToAssumeRole"
		effect  = "Allow"
		actions = ["sts:AssumeRole"]

		principals {
			type        = "Service"
			identifiers = ["scheduler.amazonaws.com"]
		}
	}
}

resource "aws_iam_role" "scheduler_start_state_machine" {
	name               = "${var.project_name}-${var.environment}-scheduler-start-state-machine"
	assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "scheduler_start_state_machine" {
	statement {
		sid    = "AllowStartSpecificStateMachine"
		effect = "Allow"

		actions = ["states:StartExecution"]

		resources = [var.step_function_state_machine_arn]
	}
}

resource "aws_iam_policy" "scheduler_start_state_machine" {
	name   = "${var.project_name}-${var.environment}-scheduler-start-state-machine"
	policy = data.aws_iam_policy_document.scheduler_start_state_machine.json
}

resource "aws_iam_role_policy_attachment" "scheduler_start_state_machine" {
	role       = aws_iam_role.scheduler_start_state_machine.name
	policy_arn = aws_iam_policy.scheduler_start_state_machine.arn
}
