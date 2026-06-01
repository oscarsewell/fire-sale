"""AWS Lambda handler for tracked product checker."""
import json
import logging

from tracked_product_checker import get_tracked_products_by_site

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """AWS Lambda handler that returns tracked products grouped by site."""
    try:
        products_by_site = get_tracked_products_by_site()

        return {
            "statusCode": 200,
            "body": json.dumps(products_by_site),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        logger.error("Lambda handler error: %s", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
