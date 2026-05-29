"""test file for notifications.py"""
import pytest
from notifications import should_notify, should_notify_percentage, evaluate_notification, create_notification_message, send_discord_notification, send_notification, send_email_notification, process_notifications
from unittest.mock import patch


def test_should_notify_when_price_below_target():
    assert should_notify(90, 100) == True


def test_should_not_notify_when_price_above_target():
    assert should_notify(110, 100) == False


def test_should_not_notify_if_price_missing():
    assert should_notify(None, 100) == False


def test_should_not_notify_if_target_missing():
    assert should_notify(90, None) == False


def test_should_notify_when_price_equals_target():
    assert should_notify(100, 100) == True


def test_should_notify_when_percentage_off_above_target():
    assert should_notify_percentage(90, 10, 100) == True


def test_should_not_notify_when_percentage_off_below_target():
    assert should_notify_percentage(95, 10, 100) == False


def test_should_not_notify_if_price_missing():
    assert should_notify_percentage(None, 10, 100) == False


def test_should_not_notify_if_target_missing():
    assert should_notify_percentage(90, None, 100) == False


def test_should_notify_when_price_equals_target():
    assert should_notify_percentage(100, 0, 100) == True


def test_evaluate_notification_should_notify_when_price_below_target():
    tracking_record = {"product_url": "https://example.com",
                       "target_price": 100, "notification_type": "email"}
    product_record = {"product_name": "Test Product", "product_url": "https://example.com",
                      "website_name": "Example", "latest_price": 90, "original_price": 120}
    result = evaluate_notification(tracking_record, product_record)

    assert result == {
        "product_name": "Test Product",
        "product_url": "https://example.com",
        "website_name": "Example",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "email"
    }


def test_evaluate_tracking_record_returns_none_when_price_is_above_target():
    tracking_record = {
        "product_url": "https://example.com/product",
        "target_price": 100,
        "notification_type": "discord",
    }

    product_record = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 120,
        "original_price": 150,
    }

    assert evaluate_notification(tracking_record, product_record) is None


def test_evaluate_tracking_record_includes_notification_destination():
    tracking_record = {
        "product_url": "https://example.com/product",
        "target_price": 100,
        "notification_type": "discord",
    }

    product_record = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
    }

    result = evaluate_notification(tracking_record, product_record)

    assert result["notification_type"] == "discord"


def test_evaluate_tracking_record_returns_none_when_price_is_missing():
    tracking_record = {
        "product_url": "https://example.com/product",
        "target_price": 100,
        "notification_type": "email",
    }

    product_record = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": None,
        "original_price": 120,
    }

    assert evaluate_notification(tracking_record, product_record) is None


def test_build_notification_message_contains_product_name():
    notification = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "discord",
    }

    message = create_notification_message(notification)

    assert "Example GPU" in message


def test_build_notification_message_contains_prices():
    notification = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "email",
    }

    message = create_notification_message(notification)

    assert "£90" in message
    assert "£120" in message
    assert "£100" in message


def test_build_notification_message_contains_product_url():
    notification = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "discord",
    }

    message = create_notification_message(notification)

    assert "https://example.com/product" in message


def test_send_notification_routes_to_discord():
    notification = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "discord",
    }

    with patch("notifications.send_discord_notification") as mock_discord:
        result = send_notification(notification)

    assert result == "discord"
    mock_discord.assert_called_once()


def test_send_notification_routes_to_email():
    notification = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "email",
    }

    with patch("notifications.send_email_notification") as mock_email:
        result = send_notification(notification)

    assert result == "email"
    mock_email.assert_called_once()


def test_send_notification_raises_error_for_unknown_type():
    notification = {
        "product_name": "Example GPU",
        "product_url": "https://example.com/product",
        "website_name": "Example Store",
        "latest_price": 90,
        "original_price": 120,
        "target_price": 100,
        "notification_type": "sms",
    }

    with pytest.raises(ValueError, match="Unsupported notification type"):
        send_notification(notification)


@patch("notifications.send_notification")
def test_process_notifications_sends_for_matching_product_below_target(mock_send):
    tracking_records = [
        {
            "product_url": "https://example.com/product",
            "target_price": 100,
            "notification_type": "email",
        }
    ]

    product_records = [
        {
            "product_name": "Example GPU",
            "product_url": "https://example.com/product",
            "website_name": "Example Store",
            "latest_price": 90,
            "original_price": 120,
        }
    ]

    result = process_notifications(tracking_records, product_records)

    assert len(result) == 1
    mock_send.assert_called_once()


@patch("notifications.send_notification")
def test_process_notifications_does_not_send_when_price_above_target(mock_send):
    tracking_records = [
        {
            "product_url": "https://example.com/product",
            "target_price": 100,
            "notification_type": "email",
        }
    ]

    product_records = [
        {
            "product_name": "Example GPU",
            "product_url": "https://example.com/product",
            "website_name": "Example Store",
            "latest_price": 120,
            "original_price": 150,
        }
    ]

    result = process_notifications(tracking_records, product_records)

    assert result == []
    mock_send.assert_not_called()


@patch("notifications.send_notification")
def test_process_notifications_skips_when_no_matching_product_record(mock_send):
    tracking_records = [
        {
            "product_url": "https://example.com/product",
            "target_price": 100,
            "notification_type": "email",
        }
    ]

    product_records = [
        {
            "product_name": "Different GPU",
            "product_url": "https://example.com/different-product",
            "website_name": "Example Store",
            "latest_price": 90,
            "original_price": 120,
        }
    ]

    result = process_notifications(tracking_records, product_records)

    assert result == []
    mock_send.assert_not_called()
