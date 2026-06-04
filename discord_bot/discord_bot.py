"""Discord bot for Hardware Hound notifications and tracking"""
import os
import discord
import asyncio
from discord.ext import tasks
from datetime import datetime
from discord import app_commands
from dotenv import load_dotenv
from urllib.parse import urlparse
from bot_db import get_or_create_product, add_tracking, get_tracked_products, remove_tracking, get_user_by_discord_id, add_price_history, update_tracking_target_price, link_discord_account
from scraper_router import full_scrape_product
from sqs_notifications import receive_discord_notifications, delete_discord_notification, parse_notification_message

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

ALLOWED_DOMAINS = {
    "ebuyer.com": "Ebuyer",
    "www.ebuyer.com": "Ebuyer",
    "overclockers.co.uk": "Overclockers",
    "www.overclockers.co.uk": "Overclockers",
    "awd-it.co.uk": "AWD-IT",
    "www.awd-it.co.uk": "AWD-IT",
}


def validate_product_url(product_url):
    """Validates that the product URL is from an allowed domain"""
    parsed_url = urlparse(product_url)
    domain = parsed_url.netloc.lower()

    if parsed_url.scheme not in ("http", "https"):
        return None

    return ALLOWED_DOMAINS.get(domain)


def validate_target_price(target_price):
    """Validates that the target price is a positive integer"""
    return target_price > 0


@client.event
async def on_ready():
    """Runs when the bot successfully logs in"""
    synced = await tree.sync()
    print(f'Logged in as {client.user}!')
    print(f'Synced {len(synced)} command(s)')

    if not discord_notification_loop.is_running():
        discord_notification_loop.start()


@tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    """Responds to /ping to confirm the bot is online"""
    await interaction.response.send_message("Woof!\nThe Hardware Hound bot is online and ready to sniff out some deals!")


@tree.command(name="track", description="Track a product by URL and target price")
async def track(
    interaction: discord.Interaction,
    product_url: str,
    target_price: int,
):
    """Responds to /track to set up tracking for a product."""
    linked_user = get_user_by_discord_id(interaction.user.id)

    if linked_user is None:
        await interaction.response.send_message(
            "Your Discord account is not linked to any account.\n\n"
            "Sign up on the Hardware Hound website to start tracking products and receiving notifications!\n"
            "https://hardwarehound.com/signup\n",
            ephemeral=True,
        )
        return

    if validate_product_url(product_url) is None:
        await interaction.response.send_message(
            "Sorry, that's not a supported product URL.\n\n"
            "Supported sites are: Ebuyer, Overclockers, and AWD-IT.",
            ephemeral=True,
        )
        return

    if not validate_target_price(target_price):
        await interaction.response.send_message(
            "Please enter a valid target price.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        product_info = await asyncio.to_thread(full_scrape_product, product_url)
    except Exception as error:
        await interaction.followup.send(
            "Sorry, there was an error fetching product details. "
            "Please check the URL and try again.\n\n"
            f"Error details: {error}",
            ephemeral=True,
        )
        return

    view = discord.ui.View(timeout=120)

    confirm_button = discord.ui.Button(
        label="Confirm Tracking",
        style=discord.ButtonStyle.green,
    )

    cancel_button = discord.ui.Button(
        label="Cancel",
        style=discord.ButtonStyle.red,
    )

    async def confirm_callback(button_interaction):
        try:
            user_id = linked_user["id"]

            product_id = get_or_create_product(
                product_url=product_info["product_url"],
                product_name=product_info["product_name"],
                site_name=product_info["site_name"],
                currency=product_info["currency"],
                page_exists=product_info["page_exists"],
            )

            add_price_history(
                product_id=product_id,
                current_price=product_info["current_price"],
                scraped_at=datetime.utcnow(),
            )

            add_tracking(
                user_id=user_id,
                product_id=product_id,
                target_price=target_price,
                original_price=product_info["original_price"] or 0,
            )

            await button_interaction.response.edit_message(
                content=(
                    "Tracking confirmed!\n\n"
                    f"Product: {product_info['product_name']}\n"
                    f"Website: {product_info['site_name']}\n"
                    f"URL: {product_info['product_url']}\n"
                    f"Target Price: £{target_price}\n"
                ),
                view=None,
            )

        except Exception as error:
            await button_interaction.response.edit_message(
                content=(
                    "Sorry, there was an error setting up tracking. "
                    "Please try again later.\n\n"
                    f"Error details: {error}"
                ),
                view=None,
            )

    async def cancel_callback(button_interaction):
        await button_interaction.response.edit_message(
            content="Tracking cancelled.",
            view=None,
        )

    confirm_button.callback = confirm_callback
    cancel_button.callback = cancel_callback

    view.add_item(confirm_button)
    view.add_item(cancel_button)

    await interaction.followup.send(
        f"You're about to track the following product:\n\n"
        f"Product: {product_info['product_name']}\n"
        f"Website: {product_info['site_name']}\n"
        f"Current Price: £{product_info['current_price']}\n"
        f"Original Price: £{product_info['original_price']}\n"
        f"Target Price: £{target_price}\n\n"
        f"URL: {product_info['product_url']}",
        view=view,
        ephemeral=True,
    )


@tree.command(name="help", description="Show Hardware Hound bot commands")
async def help_command(interaction: discord.Interaction):
    """Responds to /help to show available commands"""
    await interaction.response.send_message(
        "**Hardware Hound Bot Commands:**\n\n"
        "`/ping` - Check if the bot is online\n"
        "`/status` - Check if your Discord account is linked\n"
        "`/link` - Link your Discord account to your Hardware Hound account\n"
        "`/track` - Track a product by URL and target price\n"
        "`/list` - Show your tracked products\n"
        "`/edit` - Edit the target price for a tracked product\n"
        "`/untrack` - Stop tracking a product\n"
        "`/sites` - List supported retail sites\n"
        "`/help` - Show this help message\n",
        ephemeral=True,
    )


@tree.command(name="list", description="List your tracked products")
async def list_command(interaction: discord.Interaction):
    """Responds to /list to show the user's tracked products"""
    await interaction.response.defer(ephemeral=True)

    try:
        tracked_products = get_tracked_products(interaction.user.id)

        if not tracked_products:
            await interaction.followup.send("You aren't tracking any products yet!", ephemeral=True)
            return

        message_lines = ["**Your Tracked Products:**\n"]

        for index, product in enumerate(tracked_products, start=1):
            message_lines.append(
                f"\n**{index}. {product['product_name']}**\n"
                f"ID: {product['product_id']}\n"
                f"Store: {product['site_name']}\n"
                f"Original Price: £{product['original_price']}\n"
                f"Target Price: £{product['target_price']}\n"
                f"URL: {product['product_url']}\n"
            )

        await interaction.followup.send(
            "\n".join(message_lines),
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"Something went wrong fetching your tracked products: {e}", ephemeral=True
        )


@tree.command(name="untrack", description="Stop tracking a product")
async def untrack(
    interaction: discord.Interaction,
    product_id: int
):
    """Responds to /untrack to stop tracking a product"""
    await interaction.response.defer(ephemeral=True)

    try:
        was_removed = remove_tracking(interaction.user.id, product_id)

        if not was_removed:
            await interaction.followup.send(
                "Couldn't find that product in your tracked list.\nPlease check the product ID and try again.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Stopped tracking product ID {product_id}.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"Something went wrong trying to untrack that product: {e}", ephemeral=True
        )


@tree.command(name="status", description="Check whether your Discord account is linked")
async def status(interaction: discord.Interaction):
    """Responds to /status to check if the user's Discord account is linked to an account"""
    await interaction.response.defer(ephemeral=True)

    try:

        user = get_user_by_discord_id(interaction.user.id)

        if user:
            await interaction.followup.send(
                f"Your Discord account is linked to the following account:\n\n"
                f"Username: {user['username']}\n"
                f"Email: {user['email']}\n",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Your Discord account is not linked to any account.\n\n"
                "Sign up on the Hardware Hound website to start tracking products and receiving notifications!\n"
                "https://hardwarehound.com/signup\n",
                ephemeral=True
            )

    except Exception as error:
        await interaction.followup.send(
            f"Something went wrong checking your account status: {error}", ephemeral=True
        )


@tree.command(name="sites", description="List supported retail sites")
async def sites(interaction: discord.Interaction):
    """Responds to /sites to list supported retail sites"""
    await interaction.response.send_message(
        "**Supported Retail Sites:**\n\n"
        "Ebuyer\n"
        "Overclockers\n"
        "AWD-IT\n",
        ephemeral=True,
    )


@tree.command(name="link", description="Link your Discord account to your Hardware Hound account with a code")
async def link(interaction: discord.Interaction, code: str):
    """Responds to /link to link the user's Discord account to their Hardware Hound account using a code"""
    await interaction.response.defer(ephemeral=True)

    try:
        user = link_discord_account(code, interaction.user.id)

        if user is None:
            await interaction.followup.send(
                "Invalid or expired code. Please generate a new code on the Hardware Hound website and try again.\n\n"
                "https://hardwarehound.com/link-discord\n",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Successfully linked your Discord account to the following account:\n\n"
            f"Username: {user['username']}\n"
            f"Email: {user['email']}\n",
            ephemeral=True
        )

    except Exception as error:
        await interaction.followup.send(
            f"Something went wrong trying to link your account: {error}", ephemeral=True
        )


@tree.command(name="edit", description="Edit the target price for a tracked product")
async def edit(interaction: discord.Interaction, product_id: int, new_target_price: int):
    """Responds to /edit to change the target price for a tracked product"""
    await interaction.response.defer(ephemeral=True)

    if not validate_target_price(new_target_price):
        await interaction.followup.send(
            "Please enter a valid target price.",
            ephemeral=True,
        )
        return

    try:
        was_updated = update_tracking_target_price(
            interaction.user.id, product_id, new_target_price)

        if not was_updated:
            await interaction.followup.send(
                "Couldn't find that product in your tracked list.\nPlease check the product ID and try again.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Updated target price for product ID {product_id} to £{new_target_price}.",
            ephemeral=True
        )

    except Exception as error:
        await interaction.followup.send(
            f"Something went wrong trying to update that product: {error}", ephemeral=True
        )


async def send_discord_dm(discord_user_id, message):
    """Sends a notification message to a user on Discord"""
    user = await client.fetch_user(int(discord_user_id))
    await user.send(message)


@tasks.loop(seconds=30)
async def discord_notification_loop():
    """Poll SQS and send Discord notifications"""
    try:
        sqs_messages = await asyncio.to_thread(receive_discord_notifications)
    except Exception as error:
        print(f"Error receiving SQS messages: {error}")
        return

    for sqs_message in sqs_messages:
        try:
            notification = parse_notification_message(sqs_message)

            discord_user_id = notification.get("discord_user_id") or notification.get("recipient")
            message = notification.get("message")

            if discord_user_id is None or message is None:
                raise KeyError("SQS notification must include 'recipient'/'discord_user_id' and 'message'")

            await send_discord_dm(discord_user_id, message)

            await asyncio.to_thread(delete_discord_notification, sqs_message["ReceiptHandle"])

        except Exception as error:
            print(f"Error processing SQS message: {error}")

client.run(TOKEN)
