"""Discord bot for Hardware Hound notifications and tracking"""
import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from urllib.parse import urlparse
from bot_db import insert_discord_user, get_or_create_product, add_tracking, get_tracked_products, remove_tracking

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
    "scan.co.uk": "Scan",
    "www.scan.co.uk": "Scan",
}


def validate_product_url(product_url):
    """Validates that the product URL is from an allowed domain"""
    parsed_url = urlparse(product_url)
    domain = parsed_url.netloc.lower()

    if parsed_url.scheme not in ("http", "https"):
        return None

    return ALLOWED_DOMAINS.get(domain)


def validate_target_discount(target_discount):
    """Validates that the target discount is a positive integer between 1 and 100"""
    return 0 <= target_discount <= 100


@client.event
async def on_ready():
    """Runs when the bot successfully logs in"""
    await tree.sync()
    print(f'Logged in as {client.user}!')


@tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    """Responds to /ping to confirm the bot is online"""
    await interaction.response.send_message("Hardware Hound is online.")


@tree.command(name="track", description="Track a product by URL and target price")
async def track(
        interaction: discord.Interaction,
        product_url: str,
        target_price: int):
    """Responds to /track to set up tracking for a product"""
    website_name = validate_product_url(product_url)

    if website_name is None:
        await interaction.response.send_message(
            "Sorry, that's not a supported product URL.\n\n"
            "Supported sites are: Ebuyer, Overclockers, and Scan.",
            ephemeral=True
        )
        return

    if not validate_target_discount(target_price):
        await interaction.response.send_message(
            "Please enter a valid target price.",
            ephemeral=True
        )
        return

    view = discord.ui.View(timeout=None)

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
            discord_user_id = button_interaction.user.id

            user_id = insert_discord_user(
                discord_user_id, username=button_interaction.user.name)

            product_id = get_or_create_product(
                product_url=product_url, product_name="Not set", site_name=website_name, currency="GBP",)

            add_tracking(user_id=user_id, product_id=product_id,
                         target_price=target_price, original_price=0)

            await button_interaction.response.edit_message(
                content=(
                    "Tracking confirmed!\n\n"
                    f"Website: {website_name}\n\n"
                    f"URL: {product_url}\n\n"
                    f"Target Price: {target_price}\n"
                ),
                view=None
            )

        except Exception as e:
            await button_interaction.response.edit_message(
                content=(
                    "Sorry, there was an error setting up tracking. Please try again later.\n\n"
                    f"Error details: {str(e)}"
                ),
                view=None
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

    await interaction.response.send_message(
        f"You're about to track the following product:\n\n"
        f"Website: {website_name}\n\n"
        f"Product URL: {product_url}\n\n"
        f"Target Price: {target_price}\n\n",
        view=view,
        ephemeral=True
    )


@tree.command(name="help", description="Show Hardware Hound bot commands")
async def help_command(interaction: discord.Interaction):
    """Responds to /help to show available commands"""
    await interaction.response.send_message(
        "**Hardware Hound Bot Commands:**\n\n"
        "`/ping` - Check if the bot is online\n"
        "`/track` - Track a product by URL and target price\n"
        "`/list` - Show your tracked products\n"
        "`/untrack` - Stop tracking a product\n"
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
                f"\n**{index}. {product['product_name']}**"
                f"ID: {product['product_id']}\n"
                f"Store: {product['site_name']}\n"
                f"Original Price: {product['currency']}{product['original_price']}\n"
                f"Target Price: {product['currency']}{product['target_price']}\n"
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

client.run(TOKEN)
