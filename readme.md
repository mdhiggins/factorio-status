# Factorio Discord Bot

This Discord bot provides real-time status updates for a Factorio server, including player count, server uptime, and more. Server status will be pinned to the channel and interval messages will be sent when a player leaves or joins the server

## Prerequisites

- Docker
- Discord Bot Token
- Factorio Server with RCON enabled

## Discord Bot Permissions

- `bot`
  - Send Messages
  - Manage Messages
  - Use Slash Commands
- `applications.commands`

## Command

`/factorio-status` will send the latest server status before the next interval update

## Version Tags

|Tag|Description|
|---|---|
|latest|Stable release|

## Usage

### docker-compose
See the docker-compose.yml file for a sample setup

## Environment Variables
|Variable|Description|
|---|---|
|DISCORD_TOKEN|Your Discord bot token|
|DISCORD_CHANNEL_ID|Discord channel ID where the bot will post|
|FACTORIO_SERVER_IP|IP or address to connect to your Factorio server|
|FACTORIO_RCON_PORT|Port|
|FACTORIO_RCON_PASSWORD|RCON password (different from game password)|
|CHECK_INTERVAL|60|
