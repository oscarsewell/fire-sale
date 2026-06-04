"""Assesses whether a notification should be sent, and sends it to the right service if so."""
from currency_symbols import CurrencySymbols


def get_currency_symbol(currency_code):
    """Returns the currency symbol for a given currency code."""
    return CurrencySymbols.get_symbol(currency_code) or currency_code


def should_notify_price(latest_price, target_price, original_price):
    """Determines whether a notification should be sent based on whether the latest price has dropped to or below the target price."""
    if latest_price is None or target_price is None:
        return False

    return latest_price <= target_price


def evaluate_notification(tracking_record, product_record):
    """Evaluates whether a notification should be sent for each tracking record based on if the price has dropped below the target"""

    latest_price = product_record.get('latest_price')
    target_price = tracking_record.get('target_price')
    original_price = tracking_record.get('original_price')

    should_send = should_notify_price(
        latest_price, target_price, original_price)

    if not should_send:
        return None

    return {
        "user_id": tracking_record.get('user_id'),
        "email": tracking_record.get('email'),
        "discord": tracking_record.get('discord'),
        "product_id": product_record.get('product_id'),
        "product_url": product_record.get('product_url'),
        "website_name": product_record.get('website_name'),
        "currency": product_record.get('currency'),
        "latest_price": latest_price,
        "original_price": original_price,
        "target_price": target_price,
    }


def create_notification_message(notification_data):
    """Creates a notification message based on the notification data."""

    currency_symbol = get_currency_symbol(notification_data['currency'])

    return (
        f"Price Alert for: {notification_data['product_id']}\n\n"
        f"Your tracked product is now available for {currency_symbol}{notification_data['latest_price']}!\n\n"
        f"Original Price: {currency_symbol}{notification_data['original_price']}\n"
        f"Target Price: {currency_symbol}{notification_data['target_price']}\n\n"
        f"Check it out here: {notification_data['product_url']}"
    )


def send_discord_notification(notification_data):
    """Creates a Discord notification object."""
    message = create_notification_message(notification_data)

    return {
        "recipient": notification_data.get('discord'),
        "channel": "discord",
        "message": message,
        "product_id": notification_data.get('product_id'),
        "user_id": notification_data.get('user_id')
    }


def send_email_notification(notification_data):
    """Creates an email notification object for SES to send."""
    message = create_notification_message(notification_data)

    return {
        "recipient": notification_data.get('email'),
        "channel": "email",
        "subject": f"Price Alert: {notification_data['product_id']} - {notification_data['website_name']}",
        "body": message,
        "product_id": notification_data.get('product_id'),
        "user_id": notification_data.get('user_id')
    }


def send_notification(notification_data):
    """Creates notifications for available channels (email and/or discord).

    Returns a list of notification objects for each available channel."""
    notifications = []

    # Send email if available
    if notification_data.get('email'):
        email_notification = send_email_notification(notification_data)
        notifications.append(email_notification)

    # Send Discord if available
    if notification_data.get('discord'):
        discord_notification = send_discord_notification(notification_data)
        notifications.append(discord_notification)

    return notifications


def process_notifications(tracking_records, product_records):
    """Processes a list of tracking records against a product record, sending notifications where appropriate.

    Returns a dictionary with 'emails' list for SES processing and 'discord' list for Discord notifications."""

    emails_to_send = []
    discord_notifications = []

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

        # send_notification now returns a list of notifications (one per channel)
        notifications = send_notification(notification)

        # Separate by channel
        for notif in notifications:
            if notif.get('channel') == 'email':
                emails_to_send.append(notif)
            elif notif.get('channel') == 'discord':
                discord_notifications.append(notif)

    return {
        "emails": emails_to_send,
        "discord": discord_notifications
    }


def get_tracking_records(db_connection):
    """Fetch all tracked products with user notification details."""
    with db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                tp.user_id,
                tp.product_id,
                tp.target_price,
                tp.original_price,
                u.email,
                u.discord,
                p.product_url,
                p.product_name,
                sn.site,
                p.currency
            FROM tracked_products tp
            JOIN users u ON tp.user_id = u.id
            JOIN products p ON tp.product_id = p.id
            JOIN site_names sn ON p.site_id = sn.id""")
        rows = cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "product_id": row[1],
            "target_price": row[2],
            "original_price": row[3],
            "email": row[4],
            "discord": row[5],
            "product_url": row[6],
            "product_name": row[7],
            "website_name": row[8],
            "currency": row[9]
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
                p.product_name,
                sn.site,
                p.currency,
                ph.current_price,
                ph.scraped_at
            FROM price_history ph
            JOIN products p ON ph.product_id = p.id
            JOIN site_names sn ON p.site_id = sn.id
            ORDER BY ph.product_id, ph.scraped_at DESC""")
        rows = cursor.fetchall()

    return [
        {
            "product_id": row[0],
            "product_url": row[1],
            "product_name": row[2],
            "website_name": row[3],
            "currency": row[4],
            "latest_price": row[5],
            "scraped_at": row[6]
        }
        for row in rows
    ]


def get_users_tracking_defunct_products(db_connection, product_ids):
    """Fetch all users tracking products that are now defunct."""
    if not product_ids:
        return []

    with db_connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                tp.user_id,
                tp.product_id,
                u.email,
                p.product_url,
                p.product_name,
                sn.site
            FROM tracked_products tp
            JOIN users u ON tp.user_id = u.id
            JOIN products p ON tp.product_id = p.id
            JOIN site_names sn ON p.site_id = sn.id
            WHERE tp.product_id = ANY(%s)""", (product_ids,))
        rows = cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "product_id": row[1],
            "email": row[2],
            "product_url": row[3],
            "product_name": row[4],
            "website_name": row[5]
        }
        for row in rows
    ]


def create_defunct_product_email(tracking_record):
    """Creates an email notification for a product that is no longer available."""
    email_body = (
        f"Product Alert: {tracking_record['product_name']}\n\n"
        f"The product you were tracking is no longer available.\n\n"
        f"Product: {tracking_record['product_name']}\n"
        f"Website: {tracking_record['website_name']}\n"
        f"URL: {tracking_record['product_url']}\n\n"
        f"We have stopped tracking this product as it no longer exists on the retailer's website."
    )

    return {
        "recipient": tracking_record.get('email'),
        "channel": "email",
        "subject": f"Product No Longer Available: {tracking_record['product_name']}",
        "body": email_body,
        "product_id": tracking_record.get('product_id'),
        "user_id": tracking_record.get('user_id')
    }


def process_defunct_products(db_connection, defunct_products):
    """Processes defunct products and creates email notifications for affected users.

    Args:
        db_connection: Database connection
        defunct_products: List of dicts with 'product_id' and 'url'

    Returns:
        List of email notification objects ready for SES
    """
    if not defunct_products:
        return []

    product_ids = [product['product_id'] for product in defunct_products]
    tracking_records = get_users_tracking_defunct_products(
        db_connection, product_ids)

    emails = []
    for tracking_record in tracking_records:
        # Only send if user has email
        if tracking_record.get('email'):
            email_notification = create_defunct_product_email(tracking_record)
            emails.append(email_notification)

    return emails
