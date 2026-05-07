import discord
import os
import random
import asyncio
import time
from discord.ext import commands
from datetime import timedelta, datetime

TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_ID = 1403449777978609674

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- STORAGE ----------------
warn_log = {}
snipe_cache = {}
mod_log_channel_id = None
start_time = time.time()


# ---------------- READY ----------------
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    print(f"Logged in as {bot.user}")


# ---------------- SNIPE ----------------
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    snipe_cache[message.channel.id] = {
        "content": message.content or "No text",
        "author": str(message.author),
        "avatar": message.author.display_avatar.url
    }


# ---------------- MODLOG ----------------
async def log(guild, title, desc):
    if not mod_log_channel_id:
        return
    ch = guild.get_channel(mod_log_channel_id)
    if ch:
        await ch.send(embed=discord.Embed(title=title, description=desc))


# =========================
# 🧠 UTILITY COMMANDS
# =========================

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")


@bot.tree.command(name="uptime")
async def uptime(interaction: discord.Interaction):
    up = int(time.time() - start_time)
    await interaction.response.send_message(f"⏱ Uptime: {up} seconds")


@bot.tree.command(name="serverstats")
async def serverstats(interaction: discord.Interaction):
    g = interaction.guild
    await interaction.response.send_message(
        f"👥 Members: {g.member_count}\n📜 Roles: {len(g.roles)}"
    )


@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=str(member))
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=str(member.joined_at))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="snipe")
async def snipe(interaction: discord.Interaction):
    data = snipe_cache.get(interaction.channel.id)
    if not data:
        return await interaction.response.send_message("Nothing to snipe")

    embed = discord.Embed(description=data["content"], title="🕵️ Snipe")
    embed.set_footer(text=data["author"])
    embed.set_thumbnail(url=data["avatar"])
    await interaction.response.send_message(embed=embed)


# =========================
# 🔐 SERVER CONTROL / SECURITY
# =========================

@bot.tree.command(name="clear")
async def clear(interaction: discord.Interaction, amount: int):
    if interaction.user.id != OWNER_ID:
        return
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message("🧹 Cleared", ephemeral=True)


@bot.tree.command(name="lockdown")
async def lockdown(interaction: discord.Interaction):
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


@bot.tree.command(name="modlog")
async def modlog(interaction: discord.Interaction, channel: discord.TextChannel):
    global mod_log_channel_id
    if interaction.user.id != OWNER_ID:
        return

    mod_log_channel_id = channel.id
    await interaction.response.send_message(f"📜 Modlog set to {channel.mention}")


# =========================
# 🎮 FUN COMMANDS
# =========================

@bot.tree.command(name="coinflip")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(random.choice(["Heads", "Tails"]))


@bot.tree.command(name="roll")
async def roll(interaction: discord.Interaction, sides: int = 6):
    await interaction.response.send_message(str(random.randint(1, sides)))


@bot.tree.command(name="8ball")
async def eightball(interaction: discord.Interaction, question: str):
    await interaction.response.send_message(random.choice([
        "Yes", "No", "Maybe", "Definitely", "Ask again"
    ]))


# =========================
# 🎮 BUTTON RPS SYSTEM
# =========================

class RPSView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.success)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.danger)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "scissors")

    async def play(self, interaction, user_choice):
        bot_choice = random.choice(["rock", "paper", "scissors"])

        result = "Tie!"
        if user_choice == bot_choice:
            result = "Tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You Win!"
        else:
            result = "You Lose!"

        await interaction.response.edit_message(
            content=f"You: {user_choice} | Bot: {bot_choice}\n**{result}**",
            view=None
        )


@bot.tree.command(name="rps")
async def rps(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Choose your move:",
        view=RPSView(interaction.user)
    )


# =========================
# 🔨 MODERATION
# =========================

@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return

    await member.kick(reason=reason)
    await log(interaction.guild, "Kick", f"{member} | {reason}")
    await interaction.response.send_message("Kicked")


@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return

    await member.ban(reason=reason)
    await log(interaction.guild, "Ban", f"{member} | {reason}")
    await interaction.response.send_message("Banned")


@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    if interaction.user.id != OWNER_ID:
        return

    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await interaction.response.send_message("Muted")


bot.run(TOKEN)
