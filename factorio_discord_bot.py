import logging
import os
from datetime import UTC, datetime

import discord
from discord.ext import tasks
from mcrcon import MCRcon

# Configuration
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", 0))
FACTORIO_SERVER_IP = os.environ.get("FACTORIO_SERVER_IP", "192.168.1.120")
FACTORIO_RCON_PORT = int(os.environ.get("FACTORIO_RCON_PORT", 27015))
FACTORIO_RCON_PASSWORD = os.environ.get("FACTORIO_RCON_PASSWORD")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 60))

# Initialize Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

last_message = None
players = []

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def get_factorio_status():
    try:
        logging.info(
            f"Attempting to connect to Factorio server at {FACTORIO_SERVER_IP}:{FACTORIO_RCON_PORT}"
        )

        with MCRcon(
            FACTORIO_SERVER_IP, FACTORIO_RCON_PASSWORD, port=FACTORIO_RCON_PORT
        ) as mcr:
            players_resp = mcr.command("/players online")
            version_resp = mcr.command("/version")
            time_resp = mcr.command("/time")

        logging.info(f"Players response: {players_resp}")
        logging.info(f"Version response: {version_resp}")
        logging.info(f"Time response: {time_resp}")

        # Parse players and their playtime
        players = []
        if "Online players" in players_resp:
            player_lines = players_resp.split("\n")[1:]  # Skip the first line
            for line in player_lines:
                if line.strip():
                    parts = line.split("(")
                    player_name = parts[0].strip()
                    playtime = (
                        parts[1].split(")")[0].strip() if len(parts) > 1 else "Unknown"
                    )
                    players.append((player_name, playtime))

        game_version = version_resp.strip()
        server_lifetime = time_resp.strip()

        status = {
            "status": "online",
            "players": players,
            "player_count": len(players),
            "game_version": game_version,
            "map_name": "Unknown",  # Factorio doesn't provide an easy way to get the map name via RCON
            "server_lifetime": server_lifetime,
        }

        logging.info(f"Server status: {status}")
        return status

    except Exception as e:
        logging.exception("Error connecting to Factorio server")
        return {"status": "offline", "error": f"Connection error: {str(e)}"}


async def get_discord_embed(status) -> discord.Embed:
    embed = discord.Embed(
        title="Factorio Server Status",
        color=discord.Color.green()
        if status["status"] == "online"
        else discord.Color.red(),
        timestamp=datetime.now(UTC),
    )

    if status["status"] == "online":
        embed.add_field(name="Status", value="🟢 Online", inline=False)
        embed.add_field(
            name="Players Online", value=f"{status['player_count']}", inline=True
        )
        embed.add_field(name="Game Version", value=status["game_version"], inline=True)
        embed.add_field(
            name="Server Lifetime", value=status["server_lifetime"], inline=False
        )

        if status["players"]:
            player_list = "\n".join([f"{player[0]}" for player in status["players"]])
            embed.add_field(name="Player List", value=player_list, inline=False)
    else:
        embed.add_field(name="Status", value="🔴 Offline", inline=False)
        embed.add_field(
            name="Error", value=status.get("error", "Unknown error"), inline=False
        )

    return embed

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_server_status():
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return

    status = await get_factorio_status()

    embed = await get_discord_embed(status)

    global last_message
    global players

    if status["status"] == "online":
        for player in status["players"]:
            if player not in players:
                await channel.send(f"**{player[0]}** joined the Factorio server")

        for player in players:
            if player not in status["players"]:
                await channel.send(f"**{player[0]}** left the Factorio server")

        players = status["players"]
    else:
        players = []

    # Check if the last message in the channel is from the bot
    if not last_message:
        pins = await channel.pins()
        for message in pins:
            if message.author == client.user:
                last_message = message
                break

    if last_message:
        # If the last message is from the bot, edit it
        await last_message.edit(embed=embed)
    else:
        # If there's no previous message from the bot, send a new one
        last_message = await channel.send(embed=embed)
        await last_message.pin()


@client.event
async def on_ready():
    logging.info(f"{client.user} has connected to Discord!")
    check_server_status.start()
    await tree.sync()  # Sync the slash commands


# Register the slash command
@tree.command(name="status", description="Manual command to check server status")
async def status(interaction: discord.Interaction):
    """Manual command to check server status"""
    status = await get_factorio_status()
    embed = await get_discord_embed(status)
    await interaction.response.send_message(embed=embed)


# Run the client
client.run(DISCORD_TOKEN)
