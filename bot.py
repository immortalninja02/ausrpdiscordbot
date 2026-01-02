import discord
from discord.ext import commands
from discord import Option
import asyncio
from datetime import datetime

import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")

# IDs from your Inventor.gg data
GUILD_ID = 1455801755756400682
SESSION_CHANNEL_ID = 1455804923433193534
PING_ROLE_ID = 1456081955119431793

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(intents=intents)

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"session_msg_id": None}

    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Global session variable (Inventor.gg equivalent)
data = load_data()
session_msg_id = data.get("session_msg_id")

@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="AUSTRALIA RP"
    )

    await bot.change_presence(
        status=discord.Status.online,
        activity=activity
    )

    print(f"Logged in as {bot.user}")


# =========================
# /startsession
# =========================
@bot.slash_command(
    name="startsession",
    description="Start a session",
    guild_ids=[GUILD_ID]
)
@commands.has_permissions(administrator=True)
async def startsession(ctx: discord.ApplicationContext):
    global session_msg_id

    await ctx.respond("Starting a session...", ephemeral=True)

    channel = bot.get_channel(SESSION_CHANNEL_ID)
    # role = ctx.guild.get_role(PING_ROLE_ID) {role.mention}

    embed = discord.Embed(
        title="AUSTRALIA RP",
        description=(
            f"A session has been started by: {ctx.author.mention}\n\n"
            f"Please join with code: **Khmpr**"
        ),
        color=discord.Color.blue()
    )

    embed.set_image(
            url="https://cdn.discordapp.com/attachments/1392447866596753428/1456443628770820237/AUSTRALIA_RP_STARTING.png?ex=69586254&is=695710d4&hm=f3a288b1036e77992ffec8aef2c859d50682fa2419fa9a4db0f2b3769c0facaa&"
        )

    session_message = await channel.send(embed=embed)
    session_msg_id = session_message.id
    data["session_msg_id"] = session_msg_id
    save_data(data)

    # Role ping (temporary)
    ping_msg = await channel.send(
        content=f"AUSRP: A session has started "
    )

    await asyncio.sleep(1)
    await ping_msg.delete()


# =========================
# /schedulesession
# =========================
from datetime import datetime, timedelta, timezone

@bot.slash_command(
    name="schedulesession",
    description="Schedule a session",
    guild_ids=[GUILD_ID]
)
@commands.has_permissions(administrator=True)
async def schedulesession(
    ctx: discord.ApplicationContext,
    time: Option(int, "Unix timestamp for when to start the session", required=True)
):
    await ctx.respond("Scheduling the session...", ephemeral=True)

    # Convert Unix timestamp → UTC datetime
    start_time = datetime.fromtimestamp(time, tz=timezone.utc)
    end_time = start_time + timedelta(hours=2)  # Example: 2-hour session

    # External events are created by passing `location`, without entity_type
    event = await ctx.guild.create_scheduled_event(
        name="Session",
        description=f"A server session created by {ctx.author.name}",
        start_time=start_time,
        end_time=end_time,
        location="ER:LC",  # REQUIRED for external events
        privacy_level=discord.ScheduledEventPrivacyLevel.guild_only
    )

    await ctx.send(f"✅ Scheduled event created: {event.name}", ephemeral=True)

# =========================
# /endsession
# =========================
@bot.slash_command(
    name="endsession",
    description="Ends the current session",
    guild_ids=[GUILD_ID]
)
@commands.has_permissions(administrator=True)
async def endsession(ctx: discord.ApplicationContext):
    global session_msg_id

    await ctx.respond("Ending the session...", ephemeral=True)

    channel = bot.get_channel(SESSION_CHANNEL_ID)

    if session_msg_id is None:
        return

    try:
        msg = await channel.fetch_message(session_msg_id)

        ended_embed = discord.Embed(
            title="Session Ended",
            description="The session has ended.\nThanks for participating!",
            color=discord.Color.red()
        )

        ended_embed.set_image(
            url="https://cdn.discordapp.com/attachments/1392447866596753428/1456443574295199866/AUSTRALIA_RP_ENDED.png?ex=69586247&is=695710c7&hm=e09d26ab410da626c42bcf47d077e687b8c77c2d5ac451b66dabe4ad3c509761&"
        )

        await msg.edit(embed=ended_embed)

        await asyncio.sleep(10)
        await msg.delete()

    except discord.NotFound:
        pass

    offline_embed = discord.Embed(
        title="Server Offline",
        description="There is no session at the moment.\nPlease wait for the next one.",
        color=discord.Color.dark_gray()
    )

    offline_embed.set_image(
    url="https://cdn.discordapp.com/attachments/1392447866596753428/1456443599326806189/AUSTRALIA_RP_OFFLINE.png?ex=6958624d&is=695710cd&hm=d7c1675da8df3556a33cefbb6a4debe7f01968a19561e3f4806659d114c5034f&"
    )

    offline_msg = await channel.send(embed=offline_embed)
    session_msg_id = offline_msg.id
    data["session_msg_id"] = session_msg_id
    save_data(data)


# =========================
# Run bot
# =========================
bot.run(TOKEN)
