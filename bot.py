import discord
import os
from discord.ext import commands
from datetime import timedelta

TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_ID = 1403449777978609674

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- WARN STORAGE ----------------
warn_log = {}

# ---------------- READY ----------------
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

    print(f"Logged in as {bot.user}")


# ---------------- OWNER CHECK ----------------
def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID


# ---------------- PING ----------------
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )


# ---------------- SET GAME ----------------
@bot.tree.command(name="setgame", description="Change bot status")
async def setgame(interaction: discord.Interaction, name: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await bot.change_presence(activity=discord.Game(name=name))
    await interaction.response.send_message(f"🎮 Status set to: {name}")


# ---------------- KICK ----------------
@bot.tree.command(name="kick", description="Kick a member")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    try:
        await interaction.response.defer()
        await member.kick(reason=reason)
        await interaction.followup.send(f"👢 Kicked {member.mention}")

    except Exception as e:
        await interaction.followup.send(f"❌ Kick failed: `{e}`")


# ---------------- BAN ----------------
@bot.tree.command(name="ban", description="Ban a member")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    try:
        await interaction.response.defer()
        await member.ban(reason=reason)
        await interaction.followup.send(f"🔨 Banned {member.mention}")

    except Exception as e:
        await interaction.followup.send(f"❌ Ban failed: `{e}`")


# ---------------- UNBAN ----------------
@bot.tree.command(name="unban", description="Unban user by ID")
async def unban(interaction: discord.Interaction, user_id: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"♻️ Unbanned {user}")

    except Exception as e:
        await interaction.response.send_message(f"❌ Unban failed: `{e}`")


# ---------------- MUTE ----------------
@bot.tree.command(name="mute", description="Timeout a member")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    try:
        await interaction.response.defer()
        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await member.timeout(until, reason=reason)
        await interaction.followup.send(f"🔇 Muted {member.mention} for {minutes} minutes")

    except Exception as e:
        await interaction.followup.send(f"❌ Mute failed: `{e}`")


# ---------------- UNMUTE ----------------
@bot.tree.command(name="unmute", description="Remove timeout")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    try:
        await member.timeout(None)
        await interaction.response.send_message(f"🔊 Unmuted {member.mention}")

    except Exception as e:
        await interaction.response.send_message(f"❌ Unmute failed: `{e}`")


# ---------------- WARN ----------------
@bot.tree.command(name="warn", description="Warn a member")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    warn_log.setdefault(member.id, []).append(reason)

    await interaction.response.send_message(
        f"⚠️ Warned {member.mention} | Total: {len(warn_log[member.id])}"
    )


# ---------------- WARNINGS ----------------
@bot.tree.command(name="warnings", description="Check warnings")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    count = len(warn_log.get(member.id, []))
    await interaction.response.send_message(
        f"📄 {member.mention} has {count} warning(s)."
    )


# ---------------- GLOBAL ERROR DEBUGGER ----------------
@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):

    async def send(msg):
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except:
            pass

    if isinstance(error, discord.Forbidden):
        await send("❌ I don't have permission OR my role is too low.")

    elif isinstance(error, discord.app_commands.errors.MissingPermissions):
        await send("❌ Missing permissions.")

    elif isinstance(error, discord.app_commands.errors.CommandInvokeError):
        await send(f"❌ Command error: `{error.original}`")

    else:
        await send(f"❌ Unexpected error: `{type(error).__name__}`")


bot.run(TOKEN)
