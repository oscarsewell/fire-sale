"""This gets the tracked products from the RDS, separates them into
the correct stores, then returns a dictionary of the products for each store."""
import json
import logging
import os
from urllib.parse import urlparse
import boto3
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

secrets_client = boto3.client("secretsmanager")


def get_base_url(url: str) -> str:
    """Extract base URL (scheme + netloc) from a full product URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_db_credentials() -> dict:
    """Retrieve database credentials from AWS Secrets Manager."""
    try:
        secret_arn = os.getenv("DB_SECRET_ARN")
        if not secret_arn:
            raise ValueError("DB_SECRET_ARN environment variable not set")

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


def get_tracked_products_by_site() -> dict:
    """Query tracked products from RDS and group by site name.
    Retrieves all products being tracked, groups them by their site name,
    and uses base URL as key for products where site hasn't been cataloged yet."""
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

        cursor = connection.cursor()

        query = """
            SELECT product_id, p.product_url, sn.site
            FROM tracked_products tp
            JOIN products p ON tp.product_id = p.id
            LEFT JOIN site_names sn ON p.site_id = sn.id
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        # Group products by site
        products_by_site = {}

        for product_id, product_url, site_name in rows:
            # Use base URL as key if site_name is NULL
            key = site_name if site_name else get_base_url(product_url)

            if key not in products_by_site:
                products_by_site[key] = []

            products_by_site[key].append(product_url)

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
