import discord
import os
import random
import time
from discord.ext import commands
from datetime import timedelta
from openai import OpenAI

# ---------------- CONFIG ----------------
TOKEN = os.environ["DISCORD_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OWNER_ID = 1403449777978609674

client = OpenAI(api_key=OPENAI_API_KEY)

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


# ---------------- AI COMMAND ----------------
@bot.tree.command(name="ai", description="Chat with AI")
async def ai(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Discord assistant. Keep replies short and clear."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        reply = response.choices[0].message.content

        if len(reply) > 1900:
            reply = reply[:1900] + "..."

        await interaction.followup.send(reply)

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")


# ---------------- UTILITY ----------------
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")


@bot.tree.command(name="uptime")
async def uptime(interaction: discord.Interaction):
    seconds = int(time.time() - start_time)
    await interaction.response.send_message(f"⏱ {seconds}s")


@bot.tree.command(name="userinfo")
async def userinfo(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=str(member))
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=str(member.joined_at))
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverstats")
async def serverstats(interaction: discord.Interaction):
    await interaction.response.defer()

    g = interaction.guild

    embed = discord.Embed(title=f"📊 {g.name}")
    embed.add_field(name="Members", value=g.member_count)
    embed.add_field(name="Roles", value=len(g.roles))
    embed.add_field(name="Owner", value=str(g.owner))

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="snipe")
async def snipe(interaction: discord.Interaction):
    data = snipe_cache.get(interaction.channel.id)

    if not data:
        return await interaction.response.send_message("Nothing to snipe.")

    embed = discord.Embed(description=data["content"])
    embed.set_footer(text=data["author"])

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
    await interaction.response.send_message(
        random.choice(["Yes", "No", "Maybe", "Definitely", "Ask again"])
    )


# ---------------- RPS BUTTONS ----------------
class RPSView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user.id

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.primary)
    async def rock(self, interaction, button):
        await self.play(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.success)
    async def paper(self, interaction, button):
        await self.play(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.danger)
    async def scissors(self, interaction, button):
        await self.play(interaction, "scissors")

    async def play(self, interaction, choice):
        bot_choice = random.choice(["rock", "paper", "scissors"])

        if choice == bot_choice:
            result = "Tie"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You Win"
        else:
            result = "You Lose"

        await interaction.response.edit_message(
            content=f"You: {choice} | Bot: {bot_choice}\n**{result}**",
            view=None
        )


@bot.tree.command(name="rps")
async def rps(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Choose:",
        view=RPSView(interaction.user)
    )


# ---------------- MODERATION ----------------
@bot.tree.command(name="kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return

    await member.kick(reason=reason)
    await interaction.response.send_message("Kicked")


@bot.tree.command(name="ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.user.id != OWNER_ID:
        return

    await member.ban(reason=reason)
    await interaction.response.send_message("Banned")


@bot.tree.command(name="mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    if interaction.user.id != OWNER_ID:
        return

    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until)
    await interaction.response.send_message("Muted")


bot.run(TOKEN)
