import discord
from discord.ext import commands, tasks
from discord import Option
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os

# =========================
# CONFIG
# =========================

TOKEN = process.env.TOKEN

GUILD_ID = 1455801755756400682
SESSION_CHANNEL_ID = 1455804923433193534
PING_ROLE_ID = 1456081955119431793
SESSION_MANAGER_ROLE_ID = 1455813443071246498  # role allowed to run commands

DATA_FILE = "data.json"

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(intents=intents)

# =========================
# DATA STORAGE
# =========================

def load_data():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        with open(DATA_FILE, "w") as f:
            json.dump({"session_msg_id": None}, f)
        return {"session_msg_id": None}

    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()
session_msg_id = data.get("session_msg_id")

# =========================
# ROLE CHECK
# =========================

def has_session_role():
    async def predicate(ctx: discord.ApplicationContext):
        role = ctx.guild.get_role(SESSION_MANAGER_ROLE_ID)
        return role in ctx.author.roles if role else False
    return commands.check(predicate)

# =========================
# ERROR HANDLER
# =========================

@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.respond(
            "You do not have permission to run this command.",
            ephemeral=True
        )

# =========================
# STATUS ROTATION
# =========================

statuses = [
    "AUSTRALIA RP",
    "Made by immortalninja",
]

status_index = 0

@tasks.loop(seconds=5)
async def rotate_status():
    global status_index

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=statuses[status_index]
    )

    await bot.change_presence(
        status=discord.Status.online,
        activity=activity
    )

    status_index = (status_index + 1) % len(statuses)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not rotate_status.is_running():
        rotate_status.start()

# =========================
# /startsession
# =========================

@bot.slash_command(
    name="startsession",
    description="Start a session",
    guild_ids=[GUILD_ID]
)
@has_session_role()
async def startsession(ctx: discord.ApplicationContext):
    global session_msg_id

    await ctx.respond("Starting a session...", ephemeral=True)

    channel = bot.get_channel(SESSION_CHANNEL_ID)
    role = ctx.guild.get_role(PING_ROLE_ID)

    # Delete previous message
    if session_msg_id:
        try:
            old_msg = await channel.fetch_message(session_msg_id)
            await old_msg.delete()
        except discord.NotFound:
            pass

    embed = discord.Embed(
        title="AUSTRALIA RP",
        description=(
            f"A session has been started by: {ctx.author.mention}\n\n"
            f"Please join with code: **AUSTRP**"
        ),
        color=discord.Color.blue()
    )

    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1392447866596753428/1456829760490438877/AUSTRALIA_RP_STARTING.png"
    )

    session_message = await channel.send(
        content=f"{role.mention}",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(
            roles=[role]
        )
    )

    session_msg_id = session_message.id
    data["session_msg_id"] = session_msg_id
    save_data(data)

# =========================
# /schedulesession
# =========================

@bot.slash_command(
    name="schedulesession",
    description="Schedule a session",
    guild_ids=[GUILD_ID]
)
@has_session_role()
async def schedulesession(
    ctx: discord.ApplicationContext,
    time: Option(int, "Unix timestamp for when to start the session", required=True)
):
    await ctx.respond("Scheduling the session...", ephemeral=True)

    start_time = datetime.fromtimestamp(time, tz=timezone.utc)
    end_time = start_time + timedelta(hours=2)

    event = await ctx.guild.create_scheduled_event(
        name="Session",
        description=f"A server session created by {ctx.author.name}",
        start_time=start_time,
        end_time=end_time,
        location="ER:LC",
        privacy_level=discord.ScheduledEventPrivacyLevel.guild_only
    )

    await ctx.send(f"Scheduled event created: **{event.name}**", ephemeral=True)

# =========================
# /endsession
# =========================

@bot.slash_command(
    name="endsession",
    description="Ends the current session",
    guild_ids=[GUILD_ID]
)
@has_session_role()
async def endsession(ctx: discord.ApplicationContext):
    global session_msg_id

    await ctx.respond("Ending the session...", ephemeral=True)

    channel = bot.get_channel(SESSION_CHANNEL_ID)

    # Delete active session message
    if session_msg_id:
        try:
            msg = await channel.fetch_message(session_msg_id)
            await msg.delete()
        except discord.NotFound:
            pass

    ended_embed = discord.Embed(
        title="Session Ended",
        description="The session has ended.\nThanks for participating!",
        color=discord.Color.red()
    )

    ended_embed.set_image(
        url="https://cdn.discordapp.com/attachments/1392447866596753428/1456829761300074631/AUSTRALIA_RP_ENDED.png"
    )

    ended_msg = await channel.send(embed=ended_embed)

    await asyncio.sleep(5)
    await ended_msg.delete()

    offline_embed = discord.Embed(
        title="Server Offline",
        description="There is no session at the moment.\nPlease wait for the next one.",
        color=discord.Color.dark_gray()
    )

    offline_embed.set_image(
        url="https://cdn.discordapp.com/attachments/1392447866596753428/1456829760876580936/AUSTRALIA_RP_OFFLINE.png"
    )

    offline_msg = await channel.send(embed=offline_embed)

    session_msg_id = offline_msg.id
    data["session_msg_id"] = session_msg_id
    save_data(data)

# =========================
# RUN BOT
# =========================

bot.run(TOKEN)
