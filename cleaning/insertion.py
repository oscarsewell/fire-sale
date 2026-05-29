"""Function for inserting cleaned data into the database."""
import os
from datetime import datetime, timezone, timedelta
import logging
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def insert_product_into_db(
        product: dict,
        connection: psycopg2.extensions.connection
) -> None:
    """Inserts the cleaned product data into the database."""
    logger.info("Inserting product into database.")

    if not isinstance(product, dict):
        logger.error("product is not a dictionary: %r", product)
        raise TypeError("product must be a dictionary.")

    required_keys = (
        "product_name", "product_id", "original_price",
        "current_price", "currency_code", "url", "website_name", "scraped_at"
    )
    missing_keys = [key for key in required_keys if key not in product]
    if missing_keys:
        logger.error("product is missing required keys: %s", missing_keys)
        raise ValueError(
            f"product is missing required keys: {', '.join(missing_keys)}"
        )

    try:
        with connection.cursor() as cursor:
            insert_query = """
                INSERT INTO price_history (product_id, current_price, original_price, scraped_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                product["product_id"],
                product["current_price"],
                product["original_price"],
                product["scraped_at"]
            ))
            connection.commit()
            logger.info("Product inserted successfully.")
    except psycopg2.DatabaseError as e:
        logger.error("Database error occurred: %s", e)
        connection.rollback()
        raise


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Debug: Check if env vars are loaded
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    logger.info("DB_NAME: %s", db_name)
    logger.info("DB_USER: %s", db_user)
    logger.info("DB_HOST: %s", db_host)
    logger.info("DB_PORT: %s", db_port)

    if not all([db_name, db_user, db_host, db_port]):
        logger.error(
            "Missing required environment variables. Please check your .env file.")
        raise ValueError("Missing required database connection parameters")

    # Example usage
    db_connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    product_test = {
        "product_id": "1",
        "product_name": "MSI GeForce RTX™ 5070 12G VENTUS 2X OC",
        "current_price": 59999,
        "original_price": 69999,
        "currency_code": "GBP",
        "url": """https://www.ebuyer.com/msi-msi-geforce-rtx-5070
        -12g-ventus-2x-oc-705988#colcode=70598803""",
        "website_name": "Ebuyer",
        "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
    }
    insert_product_into_db(product_test, db_connection)
    db_connection.close()
