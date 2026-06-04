"""Discord bot for Hardware Hound notifications and tracking"""
import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from urllib.parse import urlparse
from bot_db import insert_discord_user, get_or_create_product, add_tracking, get_tracked_products, remove_tracking, get_user_by_discord_id

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
    linked_user = get_user_by_discord_id(interaction.user.id)

    website_name = validate_product_url(product_url)

    if website_name is None:
        await interaction.response.send_message(
            "Sorry, that's not a supported product URL.\n\n"
            "Supported sites are: Ebuyer, Overclockers, and AWD-IT.",
            ephemeral=True
        )
        return

    if not validate_target_price(target_price):
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

        await button_interaction.response.edit_message(
            content=(
                "Tracking confirmed!\n\n"
                f"Website: {website_name}\n\n"
                f"URL: {product_url}\n\n"
                f"Target Price: {target_price}\n"))

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


@tree.command(name="notif", description="example hardware hound notif")
async def notif_command(interaction: discord.Interaction):
    """example notification command"""
    await interaction.response.send_message(
        "**Tracked Product Alert!**\n\n"
        "**AMD Ryzen 7 8700G Eight Core 4.2GHz (Socket AM5) APU with Radeon 780M Graphics**\n\n"
        "Now available for £259.99!\n"
        "Original Price: £278.99\n\n"
        "Grab it now: https://www.overclockers.co.uk/amd-ryzen-7-8700g-eight-core-4.2ghz-socket-am5-apu-with-radeon-780m-graph-pro-amd-01796.html\n",
        ephemeral=True,
    )


@tree.command(name="list", description="List your tracked products")
async def list_command(interaction: discord.Interaction):
    """Responds to /list to show the user's tracked products"""
    # await interaction.response.defer(ephemeral=True)

    # try:
    #     tracked_products = get_tracked_products(interaction.user.id)

    #     if not tracked_products:
    #         await interaction.followup.send("You aren't tracking any products yet!", ephemeral=True)
    #         return

    #     message_lines = ["**Your Tracked Products:**\n"]

    #     for index, product in enumerate(tracked_products, start=1):
    #         message_lines.append(
    #             f"\n**{index}. {product['product_name']}**"
    #             f"ID: {product['product_id']}\n"
    #             f"Store: {product['site_name']}\n"
    #             f"Original Price: {product['currency']}{product['original_price']}\n"
    #             f"Target Price: {product['currency']}{product['target_price']}\n"
    #             f"URL: {product['product_url']}\n"
    #         )

    #     await interaction.followup.send(
    #         "\n".join(message_lines),
    #         ephemeral=True
    #     )

    # except Exception as e:
    #     await interaction.followup.send(
    #         f"Something went wrong fetching your tracked products: {e}", ephemeral=True
    #     )

    await interaction.response.send_message(
        "**Your Tracked Products:**\n\n"
        "\n**1. AMD Ryzen 7 8700G Eight Core 4.2GHz (Socket AM5) APU with Radeon 780M Graphics**"
        "ID: 3\n"
        "Store: Overclockers\n"
        "Original Price: £278.99\n"
        "Target Price: £260\n"
        "URL: https://www.overclockers.co.uk/amd-ryzen-7-8700g-eight-core-4.2ghz-socket-am5-apu-with-radeon-780m-graph-pro-amd-01796.html\n",
        ephemeral=True,
    )


@tree.command(name="untrack", description="Stop tracking a product")
async def untrack(
    interaction: discord.Interaction,
    product_id: int
):
    """Responds to /untrack to stop tracking a product"""
    # await interaction.response.defer(ephemeral=True)

    # try:
    #     was_removed = remove_tracking(interaction.user.id, product_id)

    #     if not was_removed:
    #         await interaction.followup.send(
    #             "Couldn't find that product in your tracked list.\nPlease check the product ID and try again.",
    #             ephemeral=True
    #         )
    #         return

    #     await interaction.followup.send(
    #         f"Stopped tracking product ID {product_id}.",
    #         ephemeral=True
    #     )

    # except Exception as e:
    #     await interaction.followup.send(
    #         f"Something went wrong trying to untrack that product: {e}", ephemeral=True
    #     )
    await interaction.response.send_message(
        f"**Stopped tracking product ID: {product_id}**\n\n"
        "Name: AMD Ryzen 7 8700G Eight Core 4.2GHz (Socket AM5) APU with Radeon 780M Graphics\n"
        "Store: Overclockers\n"
        "Original Price: £278.99\n"
        "Target Price: £260\n"
        "URL: https://www.overclockers.co.uk/amd-ryzen-7-8700g-eight-core-4.2ghz-socket-am5-apu-with-radeon-780m-graph-pro-amd-01796.html\n",
        ephemeral=True,
    )


@tree.command(name="status", description="Check whether your Discord account is linked")
async def status(interaction: discord.Interaction):
    """Responds to /status to check if the user's Discord account is linked to an account"""
    await interaction.response.defer(ephemeral=True)

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
    await interaction.response.send_message(
        "Log in to your Hardware Hound account to generate a linking code.\n\n"
        "Enter the code here to link your account.",
        ephemeral=True
    )


client.run(TOKEN)
