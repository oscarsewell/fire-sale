"""Lambda handler for processing defunct products and creating notifications."""
import json
import logging
import os
import psycopg2
import boto3
from dotenv import load_dotenv
from notifications import (
    process_defunct_products,
    process_notifications,
    get_tracking_records,
    get_product_records
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

secrets_client = boto3.client("secretsmanager")


def get_db_credentials() -> dict:
    """Retrieve database credentials from environment or AWS Secrets Manager."""
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    if all([host, user, password, port, dbname]):
        logger.info("Using credentials from environment variables")
        return {
            "host": host,
            "port": int(port),
            "username": user,
            "password": password,
            "dbname": dbname,
        }

    try:
        secret_arn = os.getenv("DB_SECRET_ARN")
        if not secret_arn:
            raise ValueError(
                "DB_SECRET_ARN not set and environment variables incomplete."
            )

        logger.info("Using credentials from AWS Secrets Manager")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        credentials = json.loads(response["SecretString"])

        return {
            "host": credentials.get("host"),
            "port": int(credentials.get("port", 5432)),
            "username": credentials.get("username"),
            "password": credentials.get("password"),
            "dbname": credentials.get("dbname"),
        }
    except Exception as e:
        logger.error("Failed to retrieve database credentials: %s", str(e))
        raise


def lambda_handler(event: dict, context) -> dict:
    """Lambda handler for processing notifications from the cleaning and tracking pipeline.

    Processes two types of notifications:
    1. Defunct product notifications - for products that no longer exist
    2. Price alert notifications - for products that have dropped below target price

    Args:
        event: Dict with structure:
            {
                "inserted": <count>,
                "defunct_products": [
                    {"product_id": ..., "url": ...},
                    ...
                ]
            }
        context: Lambda context object

    Returns:
        {
            "statusCode": 200 or 500,
            "body": {
                "emails": [...],
                "discord": [...]
            }
        }
    """
    load_dotenv()

    try:
        credentials = get_db_credentials()
        connection = psycopg2.connect(
            host=credentials["host"],
            port=credentials["port"],
            user=credentials["username"],
            password=credentials["password"],
            database=credentials["dbname"]
        )

        try:
            all_emails = []
            all_discord = []

            # Process defunct products
            defunct_products = event.get('defunct_products', [])
            if defunct_products:
                defunct_emails = process_defunct_products(
                    connection, defunct_products)
                all_emails.extend(defunct_emails)
                logger.info(
                    "Processed %d defunct products, created %d notifications",
                    len(defunct_products),
                    len(defunct_emails)
                )

            # Process price alert notifications
            tracking_records = get_tracking_records(connection)
            product_records = get_product_records(connection)

            if tracking_records and product_records:
                notification_result = process_notifications(
                    tracking_records, product_records)
                all_emails.extend(notification_result.get('emails', []))
                all_discord.extend(notification_result.get('discord', []))
                logger.info(
                    "Processed price alerts: %d emails, %d discord notifications",
                    len(notification_result.get('emails', [])),
                    len(notification_result.get('discord', []))
                )

            response_body = {
                "emails": all_emails,
                "discord": all_discord
            }

            logger.info(
                "Total notifications: %d emails, %d discord",
                len(all_emails),
                len(all_discord)
            )

            return {
                "statusCode": 200,
                "body": response_body
            }
        finally:
            connection.close()

    except Exception as e:
        logger.error("Error processing notifications: %s", str(e))
        return {
            "statusCode": 500,
            "body": {
                "emails": [],
                "discord": []
            }
        }
