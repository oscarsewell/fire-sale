"""Tests for the awd-it Lambda handler."""
import json
import pytest
from unittest.mock import patch
from lambda_handler import lambda_handler


def test_lambda_handler_filters_awd_it_products():
    """Test that lambda_handler only processes awd-it products."""
    mock_products_by_site = {
        "awd-it": [[1, "https://www.awd-it.co.uk/product/1"]],
        "ebuyer": [[2, "https://www.ebuyer.com/product/2"]],
    }

    mock_scraped = [
        {
            "product_id": 1,
            "url": "https://www.awd-it.co.uk/product/1",
            "current_price": "£100",
            "currency_code": "GBP",
            "page_exists": True,
            "scraped_at": "2024-01-01T00:00:00"
        }
    ]

    with patch("lambda_handler.scrape_all_products", return_value=mock_scraped):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 1
    assert body[0]["product_id"] == 1
    assert "ebuyer" not in json.dumps(body)  # Ensure ebuyer wasn't processed


def test_lambda_handler_ignores_other_sites():
    """Test that lambda_handler ignores products from non-awd-it sites."""
    mock_products_by_site = {
        "ebuyer": [[2, "https://www.ebuyer.com/product/2"]],
        "overclockers": [[3, "https://www.overclockers.co.uk/product/3"]],
    }

    with patch("lambda_handler.scrape_all_products", return_value=[]):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 0


def test_lambda_handler_empty_awd_it_site():
    """Test that lambda_handler handles empty awd-it product list."""
    mock_products_by_site = {
        "awd-it": [],
        "ebuyer": [[2, "https://www.ebuyer.com/product/2"]],
    }

    with patch("lambda_handler.scrape_all_products", return_value=[]):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 0


def test_lambda_handler_missing_awd_it_site():
    """Test that lambda_handler handles missing awd-it site gracefully."""
    mock_products_by_site = {
        "ebuyer": [[2, "https://www.ebuyer.com/product/2"]],
    }

    with patch("lambda_handler.scrape_all_products", return_value=[]):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 0


def test_lambda_handler_transforms_output_format():
    """Test that lambda_handler passes through page_exists."""
    mock_products_by_site = {
        "awd-it": [[1, "https://www.awd-it.co.uk/product/1"]],
    }

    mock_scraped = [
        {
            "product_id": 1,
            "url": "https://www.awd-it.co.uk/product/1",
            "current_price": None,
            "currency_code": None,
            "page_exists": False,
            "scraped_at": None
        }
    ]

    with patch("lambda_handler.scrape_all_products", return_value=mock_scraped):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "page_exists" in body[0]
    assert body[0]["page_exists"] is False
    assert "exists" not in body[0]
    assert "currency_code" not in body[0]


def test_lambda_handler_success_response_format():
    """Test that lambda_handler returns proper response format."""
    mock_products_by_site = {
        "awd-it": [[1, "https://www.awd-it.co.uk/product/1"]],
    }

    mock_scraped = [
        {
            "product_id": 1,
            "url": "https://www.awd-it.co.uk/product/1",
            "current_price": "£100",
            "currency_code": "GBP",
            "page_exists": True,
            "scraped_at": "2024-01-01T00:00:00"
        }
    ]

    with patch("lambda_handler.scrape_all_products", return_value=mock_scraped):
        response = lambda_handler(mock_products_by_site, {})

    assert "statusCode" in response
    assert "body" in response
    assert "headers" in response
    assert response["headers"]["Content-Type"] == "application/json"
    assert response["statusCode"] == 200


def test_lambda_handler_error_handling():
    """Test that lambda_handler handles errors gracefully."""
    mock_products_by_site = {
        "awd-it": [[1, "https://www.awd-it.co.uk/product/1"]],
    }

    with patch("lambda_handler.scrape_all_products", side_effect=Exception("Network error")):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
    assert "Network error" in body["error"]


def test_lambda_handler_multiple_awd_it_products():
    """Test that lambda_handler processes multiple awd-it products."""
    mock_products_by_site = {
        "awd-it": [
            [1, "https://www.awd-it.co.uk/product/1"],
            [2, "https://www.awd-it.co.uk/product/2"],
        ],
    }

    mock_scraped = [
        {
            "product_id": 1,
            "url": "https://www.awd-it.co.uk/product/1",
            "current_price": "£100",
            "currency_code": "GBP",
            "page_exists": True,
            "scraped_at": "2024-01-01T00:00:00"
        },
        {
            "product_id": 2,
            "url": "https://www.awd-it.co.uk/product/2",
            "current_price": "£200",
            "currency_code": "GBP",
            "page_exists": True,
            "scraped_at": "2024-01-01T00:00:00"
        }
    ]

    with patch("lambda_handler.scrape_all_products", return_value=mock_scraped):
        response = lambda_handler(mock_products_by_site, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 2
    assert body[0]["product_id"] == 1
    assert body[1]["product_id"] == 2
