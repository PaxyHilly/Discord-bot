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
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")
    print("Slash commands synced successfully.")


# ---------------- OWNER CHECK ----------------
def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID


# ---------------- PING ----------------
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! `{latency}ms`")


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

    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 Kicked {member.mention}")


# ---------------- BAN ----------------
@bot.tree.command(name="ban", description="Ban a member")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.mention}")


# ---------------- UNBAN ----------------
@bot.tree.command(name="unban", description="Unban user by ID")
async def unban(interaction: discord.Interaction, user_id: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"♻️ Unbanned {user}")


# ---------------- MUTE ----------------
@bot.tree.command(name="mute", description="Timeout a member")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await interaction.response.send_message(f"🔇 Muted {member.mention} for {minutes} minutes")


# ---------------- UNMUTE ----------------
@bot.tree.command(name="unmute", description="Remove timeout")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await member.timeout(None)
    await interaction.response.send_message(f"🔊 Unmuted {member.mention}")


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


bot.run(TOKEN)
