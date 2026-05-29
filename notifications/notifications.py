"""Assesses whether a notification should be sent, and sends it to the right service if so."""


def should_notify(latest_price, target_price):
    """Determines whether a notification should be sent based on the latest price and the target price."""
    if latest_price is None or target_price is None:
        return False

    return latest_price <= target_price


def should_notify_percentage(latest_price, target_percentage, original_price):
    """Determines whether a notification should be sent based on the latest price and the target percentage discount."""
    if latest_price is None or target_percentage is None:
        return False

    if original_price <= 0:
        return False

    discount_percentage = (
        (original_price - latest_price) / original_price) * 100

    return discount_percentage >= target_percentage


def evaluate_notification(tracking_record, product_record):
    """Evaluates whether a notification should be sent for each tracking record based on if the price has dropped below the target"""

    latest_price = product_record.get('latest_price')
    target_price = tracking_record.get('target_price')

    should_send = should_notify(latest_price, target_price)

    if not should_send:
        return None

    return {
        "product_name": product_record.get('product_name'),
        "product_url": product_record.get('product_url'),
        "website_name": product_record.get('website_name'),
        "latest_price": latest_price,
        "original_price": product_record.get('original_price'),
        "target_price": target_price,
        "notification_type": tracking_record.get('notification_type')
    }


def create_notification_message(notification_data):
    """Creates a notification message based on the notification data."""

    return (
        f"Price Alert for: {notification_data['product_name']}\n\n"
        f"Your tracked product is now available for £{notification_data['latest_price']}!\n\n"
        f"Original Price: £{notification_data['original_price']}\n"
        f"Target Price: £{notification_data['target_price']}\n\n"
        f"Check it out here: {notification_data['product_url']}"
    )


def send_discord_notification(message):
    """Placeholder for sending a Discord notification."""
    print(f"Sending Discord notification:\n{message}")


def send_email_notification(message):
    """Placeholder for sending an email notification."""
    print(f"Sending Email notification:\n{message}")


def send_notification(notification_data):
    """Routes a notification to the appropriate service based on the notification type."""
    message = create_notification_message(notification_data)
    notification_type = notification_data.get('notification_type')

    if notification_type == 'discord':
        send_discord_notification(message)
        return "discord"

    if notification_type == 'email':
        send_email_notification(message)
        return "email"

    raise ValueError(f"Unsupported notification type: {notification_type}")


def process_notifications(tracking_records, product_records):
    """Processes a list of tracking records against a product record, sending notifications where appropriate."""

    sent_notifications = []

    for tracking_record in tracking_records:
        tracking_url = tracking_record.get('product_url')

        product_record = next(
            (
                product
                for product in product_records
                if product.get('product_url') == tracking_url
            ),
            None,
        )

        if product_record is None:
            continue

        notification = evaluate_notification(tracking_record, product_record)

        if notification is None:
            continue

        send_notification(notification)
        sent_notifications.append(notification)

    return sent_notifications


def get_tracking_records(db_connection):
    """Fetch all tracked products from the tracking table."""
    with db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT product_url, target_price, notification_type
            FROM tracking""")
        rows = cursor.fetchall()

    return [
        {
            "product_url": row[0],
            "target_price": row[1],
            "notification_type": row[2]
        }
        for row in rows
    ]


def get_product_records(db_connection):
    """Fetch the latest scraped records for each product URL"""
    with db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ON (product_url)
             product_name, product_url, website_name, latest_price, original_price, scraped_at
            FROM product_data
            ORDER BY product_url, scraped_at DESC""")
        rows = cursor.fetchall()

    return [
        {
            "product_name": row[0],
            "product_url": row[1],
            "website_name": row[2],
            "latest_price": row[3],
            "original_price": row[4],
            "scraped_at": row[5]
        }
        for row in rows
    ]
