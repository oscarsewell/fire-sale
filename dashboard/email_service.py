"""AWS SES email sender for Fire Sale verification emails."""
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def _ses_client():
    region = os.getenv("SES_REGION", os.getenv("AWS_REGION", "eu-west-2"))
    return boto3.client("ses", region_name=region)


def send_verification_email(recipient: str, token: str, app_url: str) -> None:
    """
    Send an HTML + plain-text verification email via AWS SES.

    Raises RuntimeError if SES rejects the send request so the caller
    can surface a meaningful error to the user.
    """
    sender = os.getenv("SES_SENDER_EMAIL")
    if not sender:
        raise EnvironmentError(
            "SES_SENDER_EMAIL environment variable is not set.")

    # Strip trailing slash so the URL is always clean
    base = app_url.rstrip("/")
    verify_url = f"{base}/?verify={token}"

    subject = "Verify your Fire Sale account"

    body_text = (
        "Welcome to Fire Sale!\n\n"
        "Please verify your email address by visiting the link below.\n"
        "The link expires in 24 hours.\n\n"
        f"{verify_url}\n\n"
        "If you did not create an account, you can safely ignore this email."
    )

    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 24px;">
        <h2 style="color: #e63946;">🔥 Fire Sale</h2>
        <p>Thanks for signing up! Please verify your email address to activate your account.</p>
        <p>
          <a href="{verify_url}"
             style="display:inline-block; padding:12px 24px; background:#e63946;
                    color:#fff; text-decoration:none; border-radius:4px; font-weight:bold;">
            Verify my email
          </a>
        </p>
        <p style="color:#666; font-size:13px;">
          This link expires in <strong>24 hours</strong>.<br>
          If the button doesn't work, copy and paste this URL into your browser:<br>
          <a href="{verify_url}" style="color:#e63946;">{verify_url}</a>
        </p>
        <hr style="border:none; border-top:1px solid #eee;">
        <p style="color:#999; font-size:12px;">
          If you did not create a Fire Sale account, you can safely ignore this email.
        </p>
      </body>
    </html>
    """

    try:
        _ses_client().send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Verification email sent to %s", recipient)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        logger.error("SES send failed (%s): %s", error_code, exc)
        raise RuntimeError(
            f"Could not send verification email ({error_code}). "
            "Please try again or contact support."
        ) from exc
