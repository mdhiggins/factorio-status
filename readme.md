# Factorio Discord Bot

This Discord bot provides real-time status updates for a Factorio server, including player count, server uptime, and more.

## Prerequisites

- Docker
- Discord Bot Token
- Factorio Server with RCON enabled

## Setup

1. Clone this repository:
git clone git@github.com:EricBriscoe/factorio-status.git
cd factorio-status


2. Create a `.env` file in the project root with the following content:
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id
FACTORIO_SERVER_IP=your_factorio_server_ip
FACTORIO_SERVER_PORT=34197
FACTORIO_RCON_PORT=27015
FACTORIO_SERVER_PASSWORD=your_factorio_rcon_password
CHECK_INTERVAL=300


Replace the values with your actual Discord bot token, channel ID, Factorio server details, and desired check interval.

3. Build the Docker image:
docker build -t factorio-discord-bot .


4. Run the Docker container:
docker run --env-file .env factorio-discord-bot
