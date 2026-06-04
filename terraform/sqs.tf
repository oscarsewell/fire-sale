resource "aws_sqs_queue" "discord_notifications_dlq" {
  name = "hardware-hound-discord-notifications-dlq"
}

resource "aws_sqs_queue" "discord_notifications" {
  name = "hardware-hound-discord-notifications"

  visibility_timeout_seconds = 60
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 20     # long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.discord_notifications_dlq.arn
    maxReceiveCount     = 3
  })
}

output "discord_notifications_queue_url" {
  value = aws_sqs_queue.discord_notifications.url
}

output "discord_notifications_queue_arn" {
  value = aws_sqs_queue.discord_notifications.arn
}