"""SQS helpers for Discord notifications"""

import json
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

QUEUE_URL = os.getenv("DISCORD_NOTIFICATION_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")

sqs = boto3.client("sqs", region_name=AWS_REGION)


def receive_discord_notifications():
    """Receive pending Discord notification messages from SQS"""
    if QUEUE_URL is None:
        raise RuntimeError(
            "DISCORD_NOTIFICATION_QUEUE_URL environment variable is not set.")

    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,
    )

    return response.get("Messages", [])


def delete_discord_notification(receipt_handle):
    """Delete a processed message from the SQS queue"""
    if QUEUE_URL is None:
        raise RuntimeError(
            "DISCORD_NOTIFICATION_QUEUE_URL environment variable is not set.")

    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=receipt_handle
    )


def parse_notification_message(message):
    """Parse the SQS notification body"""
    return json.loads(message["Body"])
