"""Tests for the Lambda handler."""
import json
import pytest
from unittest.mock import Mock, patch
from lambda_handler import lambda_handler


def test_lambda_handler_success():
    """Test that lambda_handler returns 200 with correctly formatted JSON."""
    mock_products = {
        "ebuyer": [[1, "https://www.ebuyer.com/product/1"], [2, "https://www.ebuyer.com/product/2"]],
        "overclockers": [[3, "https://www.overclockers.co.uk/product/1"]],
    }

    with patch("lambda_handler.get_tracked_products_by_site", return_value=mock_products):
        response = lambda_handler({}, {})

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"

    body = json.loads(response["body"])
    assert body == mock_products


def test_lambda_handler_empty_products():
    """Test that lambda_handler handles empty product list correctly."""
    mock_products = {}

    with patch("lambda_handler.get_tracked_products_by_site", return_value=mock_products):
        response = lambda_handler({}, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body == {}


def test_lambda_handler_single_site():
    """Test that lambda_handler correctly handles single site."""
    mock_products = {
        "ebuyer": [[1, "https://www.ebuyer.com/product/1"]],
    }

    with patch("lambda_handler.get_tracked_products_by_site", return_value=mock_products):
        response = lambda_handler({}, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body == mock_products


def test_lambda_handler_error():
    """Test that lambda_handler returns 500 on exception."""
    with patch("lambda_handler.get_tracked_products_by_site", side_effect=Exception("Database connection failed")):
        response = lambda_handler({}, {})

    assert response["statusCode"] == 500
    assert response["headers"]["Content-Type"] == "application/json"

    body = json.loads(response["body"])
    assert "error" in body
    assert "Database connection failed" in body["error"]


def test_lambda_handler_db_error():
    """Test that lambda_handler handles database errors gracefully."""
    with patch("lambda_handler.get_tracked_products_by_site", side_effect=Exception("psycopg2.DatabaseError: connection failed")):
        response = lambda_handler({}, {})

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body


def test_lambda_handler_json_serialisable():
    """Test that lambda_handler response body is valid JSON."""
    mock_products = {
        "site1": [[1, "url1"], [2, "url2"]],
        "site2": [[3, "url3"]],
    }

    with patch("lambda_handler.get_tracked_products_by_site", return_value=mock_products):
        response = lambda_handler({}, {})

    # Should not raise an exception
    body = json.loads(response["body"])
    assert isinstance(body, dict)


def test_lambda_handler_preserves_product_structure():
    """Test that lambda_handler preserves the list structure of products."""
    mock_products = {
        "ebuyer": [[1, "https://www.ebuyer.com/product/1"]],
    }

    with patch("lambda_handler.get_tracked_products_by_site", return_value=mock_products):
        response = lambda_handler({}, {})

    body = json.loads(response["body"])
    # Verify products are lists, not tuples
    assert isinstance(body["ebuyer"][0], list)
    assert body["ebuyer"][0] == [1, "https://www.ebuyer.com/product/1"]
