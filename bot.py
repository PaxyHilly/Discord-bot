import discord
import os
import random
from discord.ext import commands
from datetime import timedelta

TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_ID = 1403449777978609674

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- STORAGE ----------------
warn_log = {}
mod_log_channel_id = None
snipe_cache = {}

# ---------------- READY ----------------
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except:
        pass

    print(f"Logged in as {bot.user}")


# ---------------- MESSAGE DELETE (SNIPE) ----------------
@bot.event
async def on_message_delete(message):
    if message.content:
        snipe_cache[message.channel.id] = message.content


# ---------------- MODLOG ----------------
async def send_modlog(guild, title, desc):
    if not mod_log_channel_id:
        return

    channel = guild.get_channel(mod_log_channel_id)
    if channel:
        embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
        await channel.send(embed=embed)


# ---------------- MODLOG SET ----------------
@bot.tree.command(name="modlog", description="Set mod log channel")
async def modlog(interaction: discord.Interaction, channel: discord.TextChannel):
    global mod_log_channel_id

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    mod_log_channel_id = channel.id
    await interaction.response.send_message(f"🧾 Mod log set to {channel.mention}")


# ---------------- PING ----------------
@bot.tree.command(name="ping", description="Latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")


# ---------------- SET GAME ----------------
@bot.tree.command(name="setgame", description="Set bot status")
async def setgame(interaction: discord.Interaction, name: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await bot.change_presence(activity=discord.Game(name=name))
    await interaction.response.send_message(f"🎮 {name}")


# ---------------- USER INFO ----------------
@bot.tree.command(name="userinfo", description="User info")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=str(member))
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=str(member.joined_at))
    embed.add_field(name="Created", value=str(member.created_at))
    await interaction.response.send_message(embed=embed)


# ---------------- SERVER INFO ----------------
@bot.tree.command(name="serverinfo", description="Server info")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=g.name)
    embed.add_field(name="Members", value=g.member_count)
    embed.add_field(name="Roles", value=len(g.roles))
    await interaction.response.send_message(embed=embed)


# ---------------- FUN ----------------
@bot.tree.command(name="coinflip")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(["Heads", "Tails"]))


@bot.tree.command(name="roll")
async def roll(interaction: discord.Interaction, sides: int = 6):
    await interaction.response.send_message(str(random.randint(1, sides)))


@bot.tree.command(name="8ball")
async def eightball(interaction: discord.Interaction, question: str):
    await interaction.response.send_message(random.choice(
        ["Yes", "No", "Maybe", "Definitely", "Ask again"]
    ))


# ---------------- SNIPE ----------------
@bot.tree.command(name="snipe", description="Last deleted message")
async def snipe(interaction: discord.Interaction):
    msg = snipe_cache.get(interaction.channel.id)

    if not msg:
        return await interaction.response.send_message("Nothing to snipe.")

    await interaction.response.send_message(f"🕵️ {msg}")


# ---------------- CLEAR ----------------
@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await interaction.response.defer()
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {amount}")


# ---------------- LOCK / UNLOCK ----------------
@bot.tree.command(name="lock")
async def lock(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return

    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔒 Locked")


@bot.tree.command(name="unlock")
async def unlock(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return

    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message("🔓 Unlocked")


# ---------------- KICK ----------------
@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return

    await interaction.response.defer()
    await member.kick(reason=reason)

    await send_modlog(interaction.guild, "👢 Kick", f"{member} | {reason}")
    await interaction.followup.send("Kicked")


# ---------------- BAN ----------------
@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return

    await interaction.response.defer()
    await member.ban(reason=reason)

    await send_modlog(interaction.guild, "🔨 Ban", f"{member} | {reason}")
    await interaction.followup.send("Banned")


# ---------------- MUTE ----------------
@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    if interaction.user.id != OWNER_ID:
        return

    await interaction.response.defer()
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)

    await send_modlog(interaction.guild, "🔇 Mute", f"{member} | {minutes}m")
    await interaction.followup.send("Muted")


# ---------------- UNMUTE ----------------
@bot.tree.command(name="unmute")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message("Unmuted")


# ---------------- WARN ----------------
@bot.tree.command(name="warn")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if interaction.user.id != OWNER_ID:
        return

    warn_log.setdefault(member.id, []).append(reason)
    await interaction.response.send_message("Warned")


# ---------------- WARNINGS ----------------
@bot.tree.command(name="warnings")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    count = len(warn_log.get(member.id, []))
    await interaction.response.send_message(f"{count} warnings")


bot.run(TOKEN)
