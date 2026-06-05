"""Function for inserting cleaned data into the database."""
import json
import os
from datetime import datetime, timezone, timedelta
import logging
import boto3
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

secrets_client = boto3.client("secretsmanager")


def get_db_credentials() -> dict:
    """Retrieve database credentials from environment or AWS Secrets Manager.

    First attempts to load from environment variables (set via .env or Lambda env).
    Falls back to AWS Secrets Manager if environment variables are not found.
    """
    # Try to get credentials from environment variables first
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    # If all env vars are present, use them
    if all([host, user, password, port, dbname]):
        logger.info("Using credentials from environment variables")
        return {
            "host": host,
            "port": int(port),
            "username": user,
            "password": password,
            "dbname": dbname,
        }

    # Otherwise, try to get from AWS Secrets Manager (Lambda environment)
    try:
        secret_arn = os.getenv("DB_SECRET_ARN")
        if not secret_arn:
            raise ValueError(
                "DB_SECRET_ARN not set and environment variables incomplete. "
                "Either set DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME "
                "or set DB_SECRET_ARN for AWS Secrets Manager."
            )

        logger.info("Using credentials from AWS Secrets Manager")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        credentials = json.loads(response["SecretString"])

        # If password_secret_arn is provided instead of password, retrieve it
        password = credentials.get("password")
        if not password and credentials.get("password_secret_arn"):
            logger.info("Retrieving password from nested secret")
            password_response = secrets_client.get_secret_value(
                SecretId=credentials["password_secret_arn"]
            )
            password_secret = json.loads(password_response["SecretString"])
            password = password_secret.get("password")

        return {
            "host": credentials.get("host"),
            "port": int(credentials.get("port", 5432)),
            "username": credentials.get("username"),
            "password": password,
            "dbname": credentials.get("dbname"),
        }
    except Exception as e:
        logger.error("Failed to retrieve database credentials: %s", str(e))
        raise


def insert_product_into_db(
        product: dict,
        connection: psycopg2.extensions.connection
) -> None:
    """Inserts the cleaned product data into the database."""
    logger.info("Inserting product into database.")

    if not isinstance(product, dict):
        logger.error("product is not a dictionary: %r", product)
        raise TypeError("product must be a dictionary.")

    required_keys = ("product_id", "current_price", "scraped_at")
    missing_keys = [key for key in required_keys if key not in product]
    if missing_keys:
        logger.error("product is missing required keys: %s", missing_keys)
        raise ValueError(
            f"product is missing required keys: {', '.join(missing_keys)}"
        )

    try:
        with connection.cursor() as cursor:
            insert_query = """
                INSERT INTO price_history (product_id, current_price, scraped_at)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (
                product["product_id"],
                product["current_price"],
                product["scraped_at"]
            ))
            connection.commit()
            logger.info("Product inserted successfully.")
    except psycopg2.DatabaseError as e:
        logger.error("Database error occurred: %s", e)
        connection.rollback()
        raise


def mark_products_defunct(
        urls: list,
        connection: psycopg2.extensions.connection
) -> None:
    """Updates the products table to mark pages as no longer existing."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE products SET page_exists = FALSE WHERE product_url = ANY(%s)",
                (urls,)
            )
            connection.commit()
            logger.info("Marked %d products as defunct.", len(urls))
    except psycopg2.DatabaseError as e:
        logger.error("Database error marking products defunct: %s", e)
        connection.rollback()
        raise


if __name__ == "__main__":
    load_dotenv()  # Load .env file if it exists

    db_credentials = get_db_credentials()

    # Example usage
    db_connection = psycopg2.connect(
        dbname=db_credentials["dbname"],
        user=db_credentials["username"],
        password=db_credentials["password"],
        host=db_credentials["host"],
        port=db_credentials["port"]
    )
    product_test = {
        "product_id": "1",
        "product_name": "MSI GeForce RTX™ 5070 12G VENTUS 2X OC",
        "current_price": 59999,
        "original_price": 69999,
        "currency_code": "GBP",
        "url": "https://www.ebuyer.com/msi-msi-geforce-rtx-5070"
        "-12g-ventus-2x-oc-705988#colcode=70598803",
        "website_name": "Ebuyer",
        "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
    }
    insert_product_into_db(product_test, db_connection)
    db_connection.close()
