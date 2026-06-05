"""Lambda handler for the cleaning function."""
import logging
import psycopg2
from dotenv import load_dotenv
from cleaning import clean_product_data
from insertion import get_db_credentials, insert_product_into_db, mark_products_defunct

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def lambda_handler(event: list, context) -> dict:
    """Lambda handler for the cleaning function.

    Receives a list of scraped product dicts, cleans each one, inserts
    valid products into price_history, and marks defunct product pages
    in the products table.

    Returns:
        {
            "inserted": <count of successfully inserted products>,
            "defunct_products": [{"product_id": ..., "url": ...}, ...]
        }
    """
    load_dotenv()
    credentials = get_db_credentials()
    connection = psycopg2.connect(
        host=credentials["host"],
        port=credentials["port"],
        user=credentials["username"],
        password=credentials["password"],
        database=credentials["dbname"]
    )

    inserted = 0
    defunct_products = []

    try:
        logger.info("Received event: %s", event)
        logger.info("Event type: %s", type(event))
        for product in event:
            logger.info("Processing product: %s", product)
            cleaned = clean_product_data(product)

            if cleaned is None:
                continue

            if not cleaned["page_exists"]:
                defunct_products.append({
                    "product_id": cleaned["product_id"],
                    "url": cleaned["url"]
                })
                continue

            insert_product_into_db(cleaned, connection)
            inserted += 1

        if defunct_products:
            defunct_urls = [p["url"] for p in defunct_products]
            mark_products_defunct(defunct_urls, connection)

        logger.info(
            "Lambda complete: %d inserted, %d defunct.", inserted, len(
                defunct_products)
        )
        return {
            "inserted": inserted,
            "defunct_products": defunct_products
        }
    except Exception as e:
        logger.error("Lambda handler error: %s", str(e))
        raise
    finally:
        connection.close()
