"""AWS SES email sender for Hardware Hound.

SES integration is planned – this module currently prints the verification
link to stdout so development can proceed without a live email service.

To enable SES when ready:
  1. Set AWS_REGION and SES_FROM_EMAIL environment variables.
  2. Uncomment the boto3 block below and remove the stub section.
"""
import logging
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def send_verification_email(
    to_email: str,
    username: str,
    verification_token: str,
    base_url: str,
) -> bool:
    """Send an account-verification email to a newly registered user.

    Returns True if the email was sent successfully, False on failure.
    """
    verification_link = f"{base_url}?verify_token={verification_token}"
    region = os.getenv("AWS_REGION", "eu-west-2")
    from_email = os.getenv("SES_FROM_EMAIL")
    logger.info(
        "Sending verification email via SES: region=%s, from=%s, to=%s",
        region, from_email, to_email,
    )
    ses = boto3.client("ses", region_name=region)

    subject = "Hardware Hound – Verify your email address"
    body_text = (
        f"Hi {username},\n\n"
        f"Thanks for signing up to Hardware Hound!\n\n"
        f"Please verify your email address by clicking the link below:\n"
        f"{verification_link}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"If you didn't create this account, you can safely ignore this email."
    )
    body_html = f"""<html><body>
    <h2>Welcome to Hardware Hound!</h2>
    <p>Hi {username},</p>
    <p>Thanks for signing up! Please verify your email address:</p>
    <p><a href="{verification_link}">Verify my account</a></p>
    <p>This link expires in 24 hours.</p>
    <p>If you didn't create this account, you can safely ignore this email.</p>
    </body></html>"""
    try:
        response = ses.send_email(
            Source=from_email,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": body_text},
                    "Html": {"Data": body_html},
                },
            },
        )
        logger.info("SES send_email succeeded: MessageId=%s",
                    response["MessageId"])
        return True
    except Exception as exc:
        logger.error("SES send_email failed: %s", exc)
        return False
