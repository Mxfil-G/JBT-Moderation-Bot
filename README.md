# Discord Moderation Bot

## Overview
A feature-rich Discord moderation bot built with discord.py. This bot provides comprehensive server moderation tools including kick, ban, warn, mute, and auto-moderation capabilities.

## Recent Changes
- **2025-11-21**: Initial Replit environment setup
  - Installed Python 3.11 and Node.js 20
  - Configured workflow to run the Discord bot
  - Set up Flask keep-alive server on port 8080
  - Added .gitignore for Python and Node.js
  - Fixed requirements.txt formatting error

## Project Structure
- `main.py` - Main Discord bot code with Flask server
- `server.js` - Optional Node.js pinger service (keeps bot alive)
- `requirements.txt` - Python dependencies (discord.py, Flask)
- `package.json` - Node.js dependencies (node-cron, axios, express)
- `warns.json` - User warnings database (auto-generated)
- `config.json` - Bot configuration (auto-generated)

## Features
### Moderation Commands (Slash Commands)
- `/kick` - Kick a member from the server
- `/ban` - Ban a member from the server
- `/unban` - Unban a user by ID
- `/mute` - Mute a member
- `/unmute` - Unmute a member
- `/clear` - Clear messages (1-100)
- `/warn` - Warn a member
- `/warnings` - View a member's warnings
- `/remove_warning` - Remove a specific warning
- `/clear_warnings` - Clear all warnings from a member
- `/config` - View bot configuration

### Auto-Moderation
- Automatically deletes messages containing configured bad words
- Auto-mutes users when they reach max warnings (default: 3)

### Keep-Alive System
- Flask web server on port 8080 keeps bot online
- Optional Node.js pinger (server.js) pings bot every 5 minutes

## Required Secrets
- `DISCORD_TOKEN` - Your Discord bot token from Discord Developer Portal

## Setup Instructions
1. **Create a Discord Bot**
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to the "Bot" section and create a bot
   - Copy the bot token

2. **Configure Bot Permissions**
   - In Discord Developer Portal, go to OAuth2 > URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: Kick Members, Ban Members, Manage Messages, Manage Roles
   - Use the generated URL to invite the bot to your server

3. **Add Bot Token**
   - The bot token should be added as a Replit Secret named `DISCORD_TOKEN`

4. **Start the Bot**
   - Click the Run button to start the bot
   - Check the console for "✅ Bot is online!" message

## Configuration
The bot creates a `config.json` file with default settings:
- `bad_words`: List of auto-moderated words
- `max_warns`: Maximum warnings before auto-mute (default: 3)
- `mute_role`: Name of the mute role (default: "Muted")
- `log_channel`: Channel for logging (optional)
- `auto_mod`: Enable/disable auto-moderation (default: true)

## Port Configuration
- **Port 8080**: Node keep-alive server (Server.js)

## Deployment
This bot is configured for deployment on Replit with VM deployment type (always running).

## User Preferences
- No specific user preferences set yet

## Project Architecture
- **Language**: Python 3.11
- **Framework**: discord.py 2.6+, 
- **Architecture**: Event-driven Discord bot 
- **Data Storage**: JSON files (warns.json, config.json)
- **Keep-Alive**: Node.js pinger
