"""This gets the tracked products from the RDS, separates them into
the correct stores, then returns a dictionary of the products for each store."""
import json
import logging
import os
from urllib.parse import urlparse
import boto3
import psycopg2
from dotenv import load_dotenv  # Load environment variables from .env file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

secrets_client = boto3.client("secretsmanager")


def get_base_url(url: str) -> str:
    """Extract base domain from a product URL."""
    url = url.strip()
    # Check for invalid characters (spaces)
    if ' ' in url:
        raise ValueError(f"Invalid URL: {url} (contains spaces)")

    # Add scheme if missing for proper parsing
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    parsed = urlparse(url)

    # Verify netloc is not empty
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: could not parse domain from {url}")

    return parsed.netloc


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

        password_from_secret = credentials.get("password")
        if not password_from_secret and credentials.get("password_secret_arn"):
            password_resp = secrets_client.get_secret_value(
                SecretId=credentials["password_secret_arn"]
            )
            password_obj = json.loads(password_resp["SecretString"])
            password_from_secret = password_obj.get("password")

        if not password_from_secret:
            raise ValueError("Database password not found in Secrets Manager payload")

        return {
            "host": credentials.get("host"),
            "port": int(credentials.get("port", 5432)),
            "username": credentials.get("username"),
            "password": password_from_secret,
            "dbname": credentials.get("dbname"),
        }
    except Exception as e:
        logger.error("Failed to retrieve database credentials: %s", str(e))
        raise


def get_tracked_products_by_site() -> dict:
    """Query tracked products from RDS and group by site name.
    Retrieves all products being tracked, groups them by their site name,
    and uses base URL as key for products where site hasn't been cataloged yet."""
    if load_dotenv is not None:
        load_dotenv()  # Load .env file if it exists
    credentials = get_db_credentials()
    connection = None

    try:
        connection = psycopg2.connect(
            host=credentials["host"],
            port=credentials["port"],
            user=credentials["username"],
            password=credentials["password"],
            database=credentials["dbname"]
        )

        with connection.cursor() as cursor:
            query = """
                SELECT product_id, p.product_url, sn.site
                FROM tracked_products tp
                JOIN products p ON tp.product_id = p.id
                LEFT JOIN site_names sn ON p.site_id = sn.id
            """

            cursor.execute(query)
            rows = cursor.fetchall()

        # Group products by site
        products_by_site = {}

        for product_id, product_url, site_name in rows:
            # Use base URL as key if site_name is NULL
            key = site_name if site_name else get_base_url(product_url)

            if key not in products_by_site:
                products_by_site[key] = []

            products_by_site[key].append((product_id, product_url))

        total_products = sum(len(urls) for urls in products_by_site.values())
        logger.info(
            "Successfully retrieved %d tracked products grouped by %d sites",
            total_products,
            len(products_by_site)
        )
        return products_by_site

    except psycopg2.DatabaseError as e:
        logger.error(
            "Database error while fetching tracked products: %s", str(e)
        )
        raise
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    pass
