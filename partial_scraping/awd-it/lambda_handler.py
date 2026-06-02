"""AWS Lambda handler that scrapes product data from URLs for awd-it products"""
import json
import logging

from awd_it_scraper import scrape_all_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """AWS Lambda handler for scraping awd-it products"""
    try:
        products_by_site = event
        if isinstance(event, str):
            products_by_site = json.loads(event)
        elif isinstance(event, dict) and "body" in event:
            body = event["body"]
            products_by_site = json.loads(
                body) if isinstance(body, str) else body

        logger.info("Processing products from %d sites", len(products_by_site))

        awd_it_products = products_by_site.get("awd-it", [])

        urls_and_ids = []
        for product_id, product_url in awd_it_products:
            urls_and_ids.append((product_url, product_id))

        scraped_products = scrape_all_products(urls_and_ids)

        output_products = []
        for product in scraped_products:
            output_products.append({
                "product_id": product["product_id"],
                "url": product["url"],
                "current_price": product["current_price"],
                "scraped_at": product["scraped_at"],
                "page_exists": product["page_exists"]
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
