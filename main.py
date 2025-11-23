import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
import datetime
import json
import asyncio

# Flask app for keeping the bot alive
app = Flask('')

@app.route('/')
def home():
    return f"✅ Bot is alive! {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Get token directly from Replit Secrets
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']

# JSON data management
class JSONManager:
    def __init__(self):
        self.warns_file = 'warns.json'
        self.config_file = 'config.json'
        self.load_default_config()

    def load_default_config(self):
        default_config = {
            "bad_words": ["spam", "testbadword"],
            "max_warns": 3,
            "mute_role": "Muted",
            "auto_mod": True
        }

        if not os.path.exists(self.config_file):
            self.save_data(self.config_file, default_config)

    def load_data(self, filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self, filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def get_warns(self, user_id):
        data = self.load_data(self.warns_file)
        return data.get(str(user_id), [])

    def add_warn(self, user_id, moderator_id, reason):
        data = self.load_data(self.warns_file)
        user_id = str(user_id)

        if user_id not in data:
            data[user_id] = []

        warn_data = {
            "reason": reason,
            "moderator": moderator_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "warn_id": len(data[user_id]) + 1
        }

        data[user_id].append(warn_data)
        self.save_data(self.warns_file, data)
        return warn_data

# Initialize JSON manager
json_manager = JSONManager()

# Discord bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    print(f'📊 Serving {len(bot.guilds)} guilds')

    # Sync slash commands
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for rule breakers"))

# Custom error handler for slash commands
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    elif isinstance(error, discord.app_commands.errors.BotMissingPermissions):
        await interaction.response.send_message("❌ I don't have permission to do that.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ An error occurred: {str(error)}", ephemeral=True)

# Slash Commands
@tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="The member to kick", reason="Reason for kicking")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        await member.kick(reason=reason)

        embed = discord.Embed(
            title="🚪 Member Kicked",
            color=0xffa500,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error kicking member: {e}", ephemeral=True)

@tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="The member to ban", reason="Reason for banning")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        await member.ban(reason=reason)

        embed = discord.Embed(
            title="🔨 Member Banned",
            color=0xff0000,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error banning member: {e}", ephemeral=True)

@tree.command(name="clear", description="Clear messages from a channel")
@app_commands.describe(amount="Number of messages to clear (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 5):
    try:
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100", ephemeral=True)
            return

        deleted = await interaction.channel.purge(limit=amount)

        embed = discord.Embed(
            title="🧹 Messages Cleared",
            description=f"Deleted {len(deleted)} messages",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, delete_after=5)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error clearing messages: {e}", ephemeral=True)

@tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="The member to warn", reason="Reason for warning")
@app_commands.checks.has_permissions(kick_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    try:
        warn_data = json_manager.add_warn(member.id, interaction.user.id, reason)
        warns = json_manager.get_warns(member.id)

        embed = discord.Embed(
            title="⚠️ Member Warned",
            color=0xffff00,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        embed.add_field(name="Total Warnings", value=len(warns), inline=False)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error warning member: {e}", ephemeral=True)

@tree.command(name="warnings", description="View a member's warnings")
@app_commands.describe(member="The member to check")
@app_commands.checks.has_permissions(kick_members=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):
    try:
        warns = json_manager.get_warns(member.id)

        if not warns:
            await interaction.response.send_message(f"✅ {member.mention} has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📋 Warnings for {member.display_name}",
            color=0xffff00
        )

        for warn in warns[-5:]:  # Show last 5 warnings
            embed.add_field(
                name=f"Warn #{warn['warn_id']}",
                value=f"Reason: {warn['reason']}\nTime: {warn['timestamp'][:16]}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error getting warnings: {e}", ephemeral=True)

@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")

# Auto-moderation
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    config = json_manager.get_config()

    if config.get('auto_mod', True):
        bad_words = config.get('bad_words', [])
        if any(word in message.content.lower() for word in bad_words):
            await message.delete()
            warning = await message.channel.send(f"🚫 {message.author.mention}, no inappropriate language!")
            await asyncio.sleep(5)
            await warning.delete()

    await bot.process_commands(message)

# Start everything
keep_alive()
bot.run(DISCORD_TOKEN)
