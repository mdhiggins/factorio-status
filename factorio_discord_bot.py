import logging
import os
from datetime import UTC, datetime

import discord
from discord.ext import commands, tasks
from mcrcon import MCRcon

# Configuration
FACTORIO_SERVER_IP = os.environ.get("FACTORIO_SERVER_IP", "192.168.1.120")
FACTORIO_SERVER_PORT = int(os.environ.get("FACTORIO_SERVER_PORT", 34197))
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", 0))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 300))
FACTORIO_RCON_PORT = int(os.environ.get("FACTORIO_RCON_PORT", 27015))
FACTORIO_SERVER_PASSWORD = os.environ.get("FACTORIO_SERVER_PASSWORD")

# Initialize Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def get_factorio_status():
    try:
        logging.info(
            f"Attempting to connect to Factorio server at {FACTORIO_SERVER_IP}:{FACTORIO_RCON_PORT}"
        )

        with MCRcon(
            FACTORIO_SERVER_IP, FACTORIO_SERVER_PASSWORD, port=FACTORIO_RCON_PORT
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


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_server_status():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return

    status = await get_factorio_status()

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

    # Check if the last message in the channel is from the bot
    last_message = None
    async for message in channel.history(limit=1):
        if message.author == bot.user:
            last_message = message
            break

    if last_message:
        # If the last message is from the bot, edit it
        await last_message.edit(embed=embed)
    else:
        # If there's no previous message from the bot, send a new one
        await channel.send(embed=embed)


@bot.command(name="status")
async def status(ctx):
    """Manual command to check server status"""
    status = await get_factorio_status()

    if status["status"] == "online":
        response = f"Server is online with {status['player_count']} players\n"
        response += f"Server Lifetime: {status['server_lifetime']}"
        if status["players"]:
            player_list = ", ".join([f"{player[0]}" for player in status["players"]])
            response += f"\nPlayers: {player_list}"
    else:
        response = f"Server is offline: {status.get('error', 'Unknown error')}"

    await ctx.send(response)


@bot.event
async def on_ready():
    logging.info(f"{bot.user} has connected to Discord!")
    check_server_status.start()


# Run the bot
bot.run(DISCORD_TOKEN)
