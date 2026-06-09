# pylint: disable=broad-exception-caught
"""AWS SES email sender for Hardware Hound."""
import json
import logging
import os
import urllib.request

import boto3
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_task_public_ip() -> str | None:
    """Return the public IP of the running ECS Fargate task.

    Queries the ECS container metadata endpoint to discover the attached ENI,
    then calls EC2 to resolve its public IP address.  Falls back to the
    checkip.amazonaws.com reflection service if the metadata or EC2 call fails.
    Returns None if the IP cannot be determined.
    """
    metadata_uri = os.getenv("ECS_CONTAINER_METADATA_URI_V4")
    if metadata_uri:
        try:
            with urllib.request.urlopen(f"{metadata_uri}/task", timeout=3) as resp:
                task_meta = json.loads(resp.read())
            for attachment in task_meta.get("Attachments", []):
                for detail in attachment.get("Details", []):
                    if detail.get("Name") == "networkInterfaceId":
                        eni_id = detail["Value"]
                        ec2 = boto3.client(
                            "ec2",
                            region_name=os.getenv("AWS_REGION", "eu-west-2"),
                        )
                        eni_info = ec2.describe_network_interfaces(
                            NetworkInterfaceIds=[eni_id]
                        )
                        public_ip = (
                            eni_info["NetworkInterfaces"][0]
                            .get("Association", {})
                            .get("PublicIp")
                        )
                        if public_ip:
                            logger.info(
                                "Resolved ECS task public IP via ENI: %s", public_ip)
                            return public_ip
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not resolve public IP via ECS metadata/EC2: %s", exc)

    # Fallback: external IP-reflection service (works as long as outbound access exists)
    try:
        with urllib.request.urlopen(
            "https://checkip.amazonaws.com", timeout=3
        ) as resp:
            public_ip = resp.read().decode().strip()
            logger.info(
                "Resolved public IP via checkip fallback: %s", public_ip)
            return public_ip
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not resolve public IP via checkip: %s", exc)

    return None


def send_verification_email(
    to_email: str,
    username: str,
    verification_token: str,
    base_url: str | None = None,
) -> bool:
    """Send an account-verification email to a newly registered user.

    Returns True if the email was sent successfully, False on failure.
    """
    if base_url is None:
        base_url = os.getenv("APP_BASE_URL")
    if base_url is None:
        public_ip = get_task_public_ip()
        if public_ip:
            base_url = f"http://{public_ip}:8501"
        else:
            base_url = "http://localhost:8501"
            logger.warning(
                "Could not determine public IP; verification link will use localhost.")
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
