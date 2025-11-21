import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
from flask import Flask
from threading import Thread
import datetime

# Flask app for keeping the bot alive
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive! " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Load environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', '0'))  # Optional: for guild-specific commands

# JSON data management
class JSONManager:
    def __init__(self):
        self.warns_file = 'warns.json'
        self.config_file = 'config.json'
        self.load_default_config()
    
    def load_default_config(self):
        default_config = {
            "bad_words": ["spam", "testbadword", "nastyword"],
            "max_warns": 3,
            "mute_role": "Muted",
            "log_channel": None,
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
    
    def remove_warn(self, user_id, warn_id):
        data = self.load_data(self.warns_file)
        user_id = str(user_id)
        
        if user_id in data:
            data[user_id] = [w for w in data[user_id] if w['warn_id'] != warn_id]
            self.save_data(self.warns_file, data)
            return True
        return False
    
    def clear_warns(self, user_id):
        data = self.load_data(self.warns_file)
        user_id = str(user_id)
        
        if user_id in data:
            del data[user_id]
            self.save_data(self.warns_file, data)
            return True
        return False
    
    def get_config(self):
        return self.load_data(self.config_file)
    
    def update_config(self, new_config):
        self.save_data(self.config_file, new_config)

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

# Slash Commands
@tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="The member to kick", reason="Reason for kicking")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    
    embed = discord.Embed(
        title="🚪 Member Kicked",
        color=0xffa500,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="The member to ban", reason="Reason for banning")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    
    embed = discord.Embed(
        title="🔨 Member Banned",
        color=0xff0000,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="unban", description="Unban a user")
@app_commands.describe(user_id="The user ID to unban", reason="Reason for unbanning")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    try:
        user = discord.Object(id=int(user_id))
        await interaction.guild.unban(user, reason=reason)
        
        embed = discord.Embed(
            title="✅ User Unbanned",
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User ID", value=user_id, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error unbanning user: {e}")

@tree.command(name="clear", description="Clear messages from a channel")
@app_commands.describe(amount="Number of messages to clear (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 5):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Amount must be between 1 and 100", ephemeral=True)
        return
    
    deleted = await interaction.channel.purge(limit=amount)
    
    embed = discord.Embed(
        title="🧹 Messages Cleared",
        description=f"Deleted {len(deleted)} messages",
        color=0x00ff00,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    
    await interaction.response.send_message(embed=embed, delete_after=5)

@tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="The member to warn", reason="Reason for warning")
@app_commands.checks.has_permissions(kick_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    warn_data = json_manager.add_warn(member.id, interaction.user.id, reason)
    warns = json_manager.get_warns(member.id)
    
    embed = discord.Embed(
        title="⚠️ Member Warned",
        color=0xffff00,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    embed.add_field(name="Total Warnings", value=len(warns), inline=False)
    embed.add_field(name="Warn ID", value=warn_data['warn_id'], inline=False)
    
    # Auto-mute if max warns reached
    config = json_manager.get_config()
    if len(warns) >= config.get('max_warns', 3):
        mute_role = discord.utils.get(interaction.guild.roles, name=config.get('mute_role', 'Muted'))
        if not mute_role:
            mute_role = await interaction.guild.create_role(name=config.get('mute_role', 'Muted'))
            for channel in interaction.guild.channels:
                await channel.set_permissions(mute_role, speak=False, send_messages=False)
        
        await member.add_roles(mute_role)
        embed.add_field(name="🔇 Auto-muted", value="User reached max warnings", inline=False)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="warnings", description="View a member's warnings")
@app_commands.describe(member="The member to check")
@app_commands.checks.has_permissions(kick_members=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):
    warns = json_manager.get_warns(member.id)
    
    if not warns:
        await interaction.response.send_message(f"✅ {member.mention} has no warnings.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"📋 Warnings for {member.display_name}",
        color=0xffff00,
        timestamp=datetime.datetime.utcnow()
    )
    
    for warn in warns[-10:]:  # Show last 10 warnings
        moderator = interaction.guild.get_member(warn['moderator'])
        mod_name = moderator.mention if moderator else "Unknown"
        embed.add_field(
            name=f"Warn #{warn['warn_id']}",
            value=f"Reason: {warn['reason']}\nModerator: {mod_name}\nTime: {warn['timestamp'][:16]}",
            inline=False
        )
    
    embed.set_footer(text=f"Total warnings: {len(warns)}")
    await interaction.response.send_message(embed=embed)

@tree.command(name="remove_warning", description="Remove a specific warning")
@app_commands.describe(member="The member", warn_id="The warning ID to remove")
@app_commands.checks.has_permissions(kick_members=True)
async def remove_warning(interaction: discord.Interaction, member: discord.Member, warn_id: int):
    if json_manager.remove_warn(member.id, warn_id):
        await interaction.response.send_message(f"✅ Removed warning #{warn_id} from {member.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Warning not found", ephemeral=True)

@tree.command(name="clear_warnings", description="Clear all warnings from a member")
@app_commands.describe(member="The member to clear warnings from")
@app_commands.checks.has_permissions(kick_members=True)
async def clear_warnings(interaction: discord.Interaction, member: discord.Member):
    if json_manager.clear_warns(member.id):
        await interaction.response.send_message(f"✅ Cleared all warnings from {member.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ No warnings found", ephemeral=True)

@tree.command(name="mute", description="Mute a member")
@app_commands.describe(member="The member to mute", reason="Reason for muting")
@app_commands.checks.has_permissions(manage_roles=True)
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    config = json_manager.get_config()
    mute_role = discord.utils.get(interaction.guild.roles, name=config.get('mute_role', 'Muted'))
    
    if not mute_role:
        mute_role = await interaction.guild.create_role(name=config.get('mute_role', 'Muted'))
        for channel in interaction.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)
    
    await member.add_roles(mute_role, reason=reason)
    
    embed = discord.Embed(
        title="🔇 Member Muted",
        color=0x808080,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="unmute", description="Unmute a member")
@app_commands.describe(member="The member to unmute")
@app_commands.checks.has_permissions(manage_roles=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    config = json_manager.get_config()
    mute_role = discord.utils.get(interaction.guild.roles, name=config.get('mute_role', 'Muted'))
    
    if mute_role and mute_role in member.roles:
        await member.remove_roles(mute_role)
        await interaction.response.send_message(f"✅ {member.mention} has been unmuted")
    else:
        await interaction.response.send_message("❌ User is not muted or mute role doesn't exist", ephemeral=True)

@tree.command(name="config", description="View current bot configuration")
@app_commands.checks.has_permissions(administrator=True)
async def config_cmd(interaction: discord.Interaction):
    config = json_manager.get_config()
    
    embed = discord.Embed(
        title="⚙️ Bot Configuration",
        color=0x00ff00,
        timestamp=datetime.datetime.utcnow()
    )
    
    for key, value in config.items():
        embed.add_field(name=key, value=str(value), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Error handling
@kick.error
@ban.error
@clear.error
async def command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)

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
