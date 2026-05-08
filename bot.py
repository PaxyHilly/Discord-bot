import discord
import os
import random
from discord.ext import commands
from datetime import timedelta

TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_ID = 1403449777978609674

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- STORAGE ----------------
warn_log = {}
mod_log_channel_id = None


# ---------------- READY ----------------
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except:
        pass

    print(f"Logged in as {bot.user}")


# ---------------- OWNER CHECK ----------------
def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID


# ---------------- MODLOG HELPER ----------------
async def send_modlog(guild, title, description):
    if not mod_log_channel_id:
        return

    channel = guild.get_channel(mod_log_channel_id)
    if channel:
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )
        await channel.send(embed=embed)


# ---------------- SET MODLOG CHANNEL ----------------
@bot.tree.command(name="modlog", description="Set mod log channel")
async def modlog(interaction: discord.Interaction, channel: discord.TextChannel):
    global mod_log_channel_id

    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    mod_log_channel_id = channel.id
    await interaction.response.send_message(f"🧾 Mod logs set to {channel.mention}")


# ---------------- PING ----------------
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 `{round(bot.latency * 1000)}ms`")


# ---------------- SET GAME ----------------
@bot.tree.command(name="setgame", description="Change bot status")
async def setgame(interaction: discord.Interaction, name: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await bot.change_presence(activity=discord.Game(name=name))
    await interaction.response.send_message(f"🎮 Status set to: {name}")


# ---------------- USER INFO ----------------
@bot.tree.command(name="userinfo", description="Get user info")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"{member}")

    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=str(member.joined_at))
    embed.add_field(name="Created", value=str(member.created_at))
    embed.add_field(
        name="Roles",
        value=", ".join([r.name for r in member.roles if r.name != "@everyone"])
    )

    await interaction.response.send_message(embed=embed)


# ---------------- SERVER INFO ----------------
@bot.tree.command(name="serverinfo", description="Server info")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild

    embed = discord.Embed(title=g.name)
    embed.add_field(name="Members", value=g.member_count)
    embed.add_field(name="Owner", value=str(g.owner))
    embed.add_field(name="Roles", value=len(g.roles))

    await interaction.response.send_message(embed=embed)


# ---------------- FUN COMMANDS ----------------
@bot.tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(["Heads", "Tails"]))


@bot.tree.command(name="roll", description="Roll a dice")
async def roll(interaction: discord.Interaction, sides: int = 6):
    await interaction.response.send_message(f"🎲 {random.randint(1, sides)}")


@bot.tree.command(name="8ball", description="Ask 8ball")
async def eightball(interaction: discord.Interaction, question: str):
    answers = ["Yes", "No", "Maybe", "Definitely", "Ask again"]
    await interaction.response.send_message(f"🎱 {random.choice(answers)}")


# ---------------- MODERATION: KICK ----------------
@bot.tree.command(name="kick", description="Kick member")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await interaction.response.defer()

    await member.kick(reason=reason)

    await send_modlog(
        interaction.guild,
        "👢 Kick",
        f"{member} was kicked\nReason: {reason}\nBy: {interaction.user}"
    )

    await interaction.followup.send(f"Kicked {member}")


# ---------------- MODERATION: BAN ----------------
@bot.tree.command(name="ban", description="Ban member")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await interaction.response.defer()

    await member.ban(reason=reason)

    await send_modlog(
        interaction.guild,
        "🔨 Ban",
        f"{member} was banned\nReason: {reason}\nBy: {interaction.user}"
    )

    await interaction.followup.send(f"Banned {member}")


# ---------------- MODERATION: MUTE ----------------
@bot.tree.command(name="mute", description="Timeout member")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await interaction.response.defer()

    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)

    await send_modlog(
        interaction.guild,
        "🔇 Mute",
        f"{member} muted for {minutes} minutes\nBy: {interaction.user}"
    )

    await interaction.followup.send(f"Muted {member}")


# ---------------- MODERATION: UNMUTE ----------------
@bot.tree.command(name="unmute", description="Remove timeout")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    await member.timeout(None)
    await interaction.response.send_message(f"🔊 Unmuted {member}")


# ---------------- WARN SYSTEM ----------------
@bot.tree.command(name="warn", description="Warn user")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ You are not Pax.", ephemeral=True)

    warn_log.setdefault(member.id, []).append(reason)

    await interaction.response.send_message(
        f"⚠️ Warned {member} | Total: {len(warn_log[member.id])}"
    )


# ---------------- WARNINGS ----------------
@bot.tree.command(name="warnings", description="Check warnings")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    count = len(warn_log.get(member.id, []))
    await interaction.response.send_message(f"📄 {member} has {count} warnings")


bot.run(TOKEN)

