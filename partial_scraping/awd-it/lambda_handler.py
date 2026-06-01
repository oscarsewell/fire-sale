"""AWS Lambda handler that scrapes product data from URLs provided by tracked_product_checker."""
import json
import logging

from awd_it_scraper import scrape_all_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """AWS Lambda handler that scrapes product data from URLs."""
    try:
        # Parse the event - handle both direct dict and Lambda response format
        products_by_site = event
        if isinstance(event, str):
            products_by_site = json.loads(event)
        elif isinstance(event, dict) and "body" in event:
            body = event["body"]
            products_by_site = json.loads(
                body) if isinstance(body, str) else body

        logger.info("Processing products from %d sites", len(products_by_site))

        # Flatten all products into a single list of (url, product_id) tuples
        urls_and_ids = []
        for site_products in products_by_site.values():
            for product_id, product_url in site_products:
                urls_and_ids.append((product_url, product_id))

        logger.info("Scraping %d products", len(urls_and_ids))

        # Scrape all products
        scraped_products = scrape_all_products(urls_and_ids)

        # Transform to output format
        output_products = []
        for product in scraped_products:
            output_products.append({
                "product_id": product["product_id"],
                "url": product["url"],
                "current_price": product["current_price"],
                "scraped_at": product["scraped_at"],
                "page_exists": product["exists"]
            })

        logger.info("Successfully scraped %d products", len(output_products))

        return {
            "statusCode": 200,
            "body": json.dumps(output_products),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        logger.error("Scraper lambda handler error: %s", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
