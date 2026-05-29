"""Assesses whether a notification should be sent, and sends it to the right service if so."""
from currency_symbols import CurrencySymbols


def get_currency_symbol(currency_code):
    """Returns the currency symbol for a given currency code."""
    return CurrencySymbols.get_symbol(currency_code) or currency_code


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
    target_discount = tracking_record.get('target_discount')
    original_price = product_record.get('original_price')

    should_send = should_notify_percentage(
        latest_price, target_discount, original_price)

    if not should_send:
        return None

    return {
        "product_id": product_record.get('product_id'),
        "product_url": product_record.get('product_url'),
        "website_name": product_record.get('website_name'),
        "currency": product_record.get('currency'),
        "latest_price": latest_price,
        "original_price": original_price,
        "target_discount": target_discount,
        "notification_type": tracking_record.get('notification_destination'),
        "user_contact": tracking_record.get('user_contact'),
    }


def create_notification_message(notification_data):
    """Creates a notification message based on the notification data."""

    currency_symbol = get_currency_symbol(notification_data['currency'])

    return (
        f"Price Alert for: {notification_data['product_id']}\n\n"
        f"Your tracked product is now available for {currency_symbol}{notification_data['latest_price']}!\n\n"
        f"Original Price: {currency_symbol}{notification_data['original_price']}\n"
        f"Target Discount: {notification_data['target_discount']}%\n\n"
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
        tracking_product_id = tracking_record.get('product_id')

        product_record = next(
            (
                product
                for product in product_records
                if product.get('product_id') == tracking_product_id
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
    """Fetch all tracked products with user notification details."""
    with db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                tp.user_id,
                tp.product_id,
                tp.target_discount,
                u.notification_destination,
                u.user_contact,
                p.product_url,
                p.site_name,
                p.currency
            FROM tracked_products tp
            JOIN users u ON tp.user_id = u.id
            JOIN products p ON tp.product_id = p.id""")
        rows = cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "product_id": row[1],
            "target_discount": row[2],
            "notification_destination": row[3],
            "user_contact": row[4],
            "product_url": row[5],
            "website_name": row[6],
            "currency": row[7]
        }
        for row in rows
    ]


def get_product_records(db_connection):
    """Fetch the latest scraped price record for each product."""
    with db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ON (ph.product_id)
                ph.product_id,
                p.product_url,
                p.site_name,
                p.currency,
                ph.current_price,
                ph.original_price,
                ph.scraped_at
            FROM price_history ph
            JOIN products p ON ph.product_id = p.id
            ORDER BY ph.product_id, ph.scraped_at DESC""")
        rows = cursor.fetchall()

    return [
        {
            "product_id": row[0],
            "product_url": row[1],
            "website_name": row[2],
            "currency": row[3],
            "latest_price": row[4],
            "original_price": row[5],
            "scraped_at": row[6]
        }
        for row in rows
    ]
