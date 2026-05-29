"""Function for inserting cleaned data into the database."""
import psycopg2
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def insert_product_into_db(
        product: dict,
        db_connection: psycopg2.extensions.connection
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
        with db_connection.cursor() as cursor:
            insert_query = """
                INSERT INTO products (product_id, current_price, original_price, scraped_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                product["product_id"],
                product["current_price"],
                product["original_price"],
                product["scraped_at"]
            ))
            db_connection.commit()
            logger.info("Product inserted successfully.")
    except psycopg2.DatabaseError as e:
        logger.error("Database error occurred: %s", e)
        db_connection.rollback()
        raise


if __name__ == "__main__":
    # Example usage
    db_connection = psycopg2.connect(
        dbname="your_db_name",
        user="your_db_user",
        password="your_db_password",
        host="your_db_host",
        port="your_db_port"
    )
    product = {
        "product_id": "123",
        "product_name": "Apple iPhone 13 Pro Max",
        "price": 899.00,
        "currency": "USD",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    insert_product_into_db(product, db_connection)
    db_connection.close()
