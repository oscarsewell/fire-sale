"""AWS SES email sender for Hardware Hound.

SES integration is planned – this module currently prints the verification
link to stdout so development can proceed without a live email service.

To enable SES when ready:
  1. Set AWS_REGION and SES_FROM_EMAIL environment variables.
  2. Uncomment the boto3 block below and remove the stub section.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Uncomment when SES is configured:
# import boto3
# _ses = boto3.client("ses", region_name=os.getenv("AWS_REGION", "eu-west-2"))


def send_verification_email(
    to_email: str,
    username: str,
    verification_token: str,
    base_url: str,
) -> bool:
    """Send an account-verification email to a newly registered user.

    Returns True if the email was sent (or stubbed), False on failure.
    """
    verification_link = f"{base_url}?verify_token={verification_token}"

    # ── SES stub (remove once SES is configured) ─────────────────────────────
    logger.warning("SES not configured – verification link: %s",
                   verification_link)
    print(
        f"\n[Hardware Hound] Verification link for {username} <{to_email}>:\n"
        f"  {verification_link}\n"
    )
    return True
    # ─────────────────────────────────────────────────────────────────────────

    # ── Real SES implementation (uncomment when ready) ────────────────────────
    # subject = "Hardware Hound – Verify your email address"
    # body_text = (
    #     f"Hi {username},\n\n"
    #     f"Thanks for signing up to Hardware Hound!\n\n"
    #     f"Please verify your email address by clicking the link below:\n"
    #     f"{verification_link}\n\n"
    #     f"This link expires in 24 hours.\n\n"
    #     f"If you didn't create this account, you can safely ignore this email."
    # )
    # body_html = f"""<html><body>
    # <h2>Welcome to Hardware Hound!</h2>
    # <p>Hi {username},</p>
    # <p>Thanks for signing up! Please verify your email address:</p>
    # <p><a href="{verification_link}">Verify my account</a></p>
    # <p>This link expires in 24 hours.</p>
    # <p>If you didn't create this account, you can safely ignore this email.</p>
    # </body></html>"""
    # try:
    #     _ses.send_email(
    #         Source=os.getenv("SES_FROM_EMAIL"),
    #         Destination={"ToAddresses": [to_email]},
    #         Message={
    #             "Subject": {"Data": subject},
    #             "Body": {
    #                 "Text": {"Data": body_text},
    #                 "Html": {"Data": body_html},
    #             },
    #         },
    #     )
    #     return True
    # except Exception as exc:
    #     logger.error("SES send_email failed: %s", exc)
    #     return False
