"""Test file for notifications.py"""
import pytest
from unittest.mock import Mock, MagicMock
from notifications import (
    should_notify_price,
    evaluate_notification,
    create_notification_message,
    send_notification,
    process_notifications,
    get_currency_symbol,
    create_defunct_product_email,
    process_defunct_products,
    get_users_tracking_defunct_products,
)


# Tests for price notification logic
def test_should_notify_price_when_below_target():
    """Should notify when latest price is at or below target"""
    assert should_notify_price(50, 50, 100) is True
    assert should_notify_price(40, 50, 100) is True


def test_should_not_notify_price_when_above_target():
    """Should not notify when above target or missing data"""
    assert should_notify_price(60, 50, 100) is False
    assert should_notify_price(None, 50, 100) is False
    assert should_notify_price(50, None, 100) is False


def test_evaluate_notification_returns_data_when_below_target():
    """Should return notification data when price is below target"""
    tracking = {
        "user_id": 1, "product_id": 100, "target_price": 50,
        "original_price": 100, "email": "test@example.com", "discord": None
    }
    product = {
        "product_id": 100, "product_url": "https://example.com",
        "website_name": "Store", "currency": "GBP", "latest_price": 45
    }

    result = evaluate_notification(tracking, product)

    assert result is not None
    assert result["user_id"] == 1
    assert result["latest_price"] == 45


def test_evaluate_notification_returns_none_when_above_target():
    """Should return None when price is above target"""
    tracking = {
        "user_id": 1, "product_id": 100, "target_price": 50,
        "original_price": 100
    }
    product = {
        "product_id": 100, "latest_price": 60
    }

    result = evaluate_notification(tracking, product)

    assert result is None


# Tests for notification messages
def test_create_notification_message_contains_key_info():
    """Message should contain product ID, prices, and URL"""
    notification = {
        "product_id": "GPU-123", "latest_price": 50, "original_price": 100,
        "target_price": 60, "product_url": "https://example.com/product",
        "currency": "GBP"
    }

    message = create_notification_message(notification)

    assert "GPU-123" in message
    assert "£50" in message
    assert "https://example.com/product" in message


def test_create_notification_message_uses_correct_currency():
    """Message should use correct currency symbol"""
    notification = {
        "product_id": "GPU", "latest_price": 50, "original_price": 100,
        "target_price": 60, "product_url": "https://example.com",
        "currency": "USD"
    }

    message = create_notification_message(notification)

    assert "" in message


# Tests for multi-channel notification routing
def test_send_notification_routes_to_email_when_available():
    """Should return email notification when email exists"""
    notification = {
        "email": "user@example.com", "discord": None, "product_id": "GPU",
        "user_id": 1, "latest_price": 50, "original_price": 100,
        "target_price": 60, "product_url": "https://example.com",
        "website_name": "Store", "currency": "GBP"
    }

    result = send_notification(notification)

    assert len(result) == 1
    assert result[0]["channel"] == "email"


def test_send_notification_routes_to_both_channels():
    """Should return both notifications when both channels exist"""
    notification = {
        "email": "user@example.com", "discord": "user123", "product_id": "GPU",
        "user_id": 1, "latest_price": 50, "original_price": 100,
        "target_price": 60, "product_url": "https://example.com",
        "website_name": "Store", "currency": "GBP"
    }

    result = send_notification(notification)

    assert len(result) == 2
    channels = [n["channel"] for n in result]
    assert "email" in channels
    assert "discord" in channels


def test_send_notification_returns_empty_when_no_contact():
    """Should return empty list when no contact info"""
    notification = {
        "email": None, "discord": None, "product_id": "GPU", "user_id": 1
    }

    result = send_notification(notification)

    assert len(result) == 0


# Tests for batch processing
def test_process_notifications_separates_channels():
    """Should separate emails and discord notifications"""
    tracking = [
        {
            "user_id": 1, "product_id": 100, "target_price": 50,
            "original_price": 100, "email": "user1@example.com", "discord": None
        }
    ]
    products = [
        {
            "product_id": 100, "product_url": "https://example.com",
            "website_name": "Store", "currency": "GBP", "latest_price": 45
        }
    ]

    result = process_notifications(tracking, products)

    assert "emails" in result
    assert "discord" in result
    assert len(result["emails"]) == 1


def test_process_notifications_skips_non_matching_products():
    """Should skip tracking records without matching products"""
    tracking = [
        {
            "user_id": 1, "product_id": 999, "target_price": 50,
            "original_price": 100, "email": "user@example.com", "discord": None
        }
    ]
    products = [
        {
            "product_id": 100, "product_url": "https://example.com",
            "website_name": "Store", "currency": "GBP", "latest_price": 45
        }
    ]

    result = process_notifications(tracking, products)

    assert len(result["emails"]) == 0


def test_process_notifications_handles_multiple_records():
    """Should process multiple tracking records and products"""
    tracking = [
        {
            "user_id": 1, "product_id": 100, "target_price": 50,
            "original_price": 100, "email": "user1@example.com", "discord": None
        },
        {
            "user_id": 2, "product_id": 101, "target_price": 40,
            "original_price": 80, "email": None, "discord": "user2"
        }
    ]
    products = [
        {
            "product_id": 100, "product_url": "https://example.com/1",
            "website_name": "Store 1", "currency": "GBP", "latest_price": 45
        },
        {
            "product_id": 101, "product_url": "https://example.com/2",
            "website_name": "Store 2", "currency": "USD", "latest_price": 35
        }
    ]

    result = process_notifications(tracking, products)

    assert len(result["emails"]) == 1
    assert len(result["discord"]) == 1


# Tests for currency and defunct products
def test_get_currency_symbol_returns_correct_symbols():
    """Should return correct currency symbols"""
    assert get_currency_symbol("GBP") == "£"
    assert get_currency_symbol("USD") == "$"
    assert get_currency_symbol("UNKNOWN") == "UNKNOWN"


def test_create_defunct_product_email_has_correct_structure():
    """Email should have correct structure and content"""
    tracking = {
        "user_id": 1, "product_id": 100, "email": "user@example.com",
        "product_url": "https://example.com/product",
        "product_name": "GPU RTX 5070", "website_name": "Example Store"
    }

    result = create_defunct_product_email(tracking)

    assert result["recipient"] == "user@example.com"
    assert result["channel"] == "email"
    assert result["product_id"] == 100
    assert "GPU RTX 5070" in result["subject"]


def test_process_defunct_products_creates_emails_for_users_with_email():
    """Should create emails only for users with email addresses"""
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__.return_value = None
    mock_cursor.fetchall.return_value = [
        (1, 100, "user@example.com", "https://example.com/product",
         "GPU RTX 5070", "Example Store"),
        (2, 101, None, "https://example.com/product2",
         "GPU RTX 4090", "Example Store")
    ]

    mock_connection = Mock()
    mock_connection.cursor.return_value = mock_cursor

    defunct = [{"product_id": 100, "url": "https://example.com/product"},
               {"product_id": 101, "url": "https://example.com/product2"}]

    result = process_defunct_products(mock_connection, defunct)

    assert len(result) == 1
    assert result[0]["recipient"] == "user@example.com"


def test_get_users_tracking_defunct_products_queries_database():
    """Should query database and return formatted records"""
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.__exit__.return_value = None
    mock_cursor.fetchall.return_value = [
        (1, 100, "user@example.com", "https://example.com/product",
         "GPU", "Store")
    ]

    mock_connection = Mock()
    mock_connection.cursor.return_value = mock_cursor

    result = get_users_tracking_defunct_products(mock_connection, [100])

    assert len(result) == 1
    assert result[0]["user_id"] == 1
    assert result[0]["product_id"] == 100
