import discord
import os
import random
import time
from datetime import timedelta
from discord.ext import commands
from openai import OpenAI

# ================= CONFIG =================
TOKEN = os.environ["DISCORD_TOKEN"]
SAMBANOVA_API_KEY = os.environ["SAMBANOVA_API_KEY"]

OWNER_ID = 1403449777978609674

# ================= AI CLIENT =================
client = OpenAI(
    api_key=SAMBANOVA_API_KEY,
    base_url="https://api.sambanova.ai/v1"
)

# ================= DISCORD SETUP =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ================= STORAGE =================
snipe_cache = {}
start_time = time.time()

# ================= READY =================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    print(f"🤖 Logged in as {bot.user}")


# ================= MESSAGE DELETE (SNIPE) =================
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    snipe_cache[message.channel.id] = {
        "content": message.content or "No text",
        "author": str(message.author)
    }


# ================= AI COMMAND =================
@bot.tree.command(name="ai", description="Chat with AI")
async def ai(interaction: discord.Interaction, prompt: str):

    await interaction.response.defer()

    try:
        response = client.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Discord assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        reply = response.choices[0].message.content

        if not reply:
            reply = "No response."

        if len(reply) > 1900:
            reply = reply[:1900] + "..."

        await interaction.followup.send(reply)

    except Exception as e:
        await interaction.followup.send(
            f"❌ AI error:\n```{e}```"
        )


# ================= UTILITY =================
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! `{latency}ms`")


@bot.tree.command(name="uptime", description="Show bot uptime")
async def uptime(interaction: discord.Interaction):

    seconds = int(time.time() - start_time)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    await interaction.response.send_message(
        f"⏱ Uptime: `{hours}h {minutes}m {secs}s`"
    )


@bot.tree.command(name="userinfo", description="Get user info")
async def userinfo(
    interaction: discord.Interaction,
    member: discord.Member
):

    embed = discord.Embed(
        title=f"{member}",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="User ID", value=member.id)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"))
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"))

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverstats", description="Show server stats")
async def serverstats(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=discord.Color.green()
    )

    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Roles", value=len(guild.roles))
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.add_field(name="Owner", value=str(guild.owner))

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="snipe", description="Show last deleted message")
async def snipe(interaction: discord.Interaction):

    data = snipe_cache.get(interaction.channel.id)

    if not data:
        return await interaction.response.send_message(
            "❌ Nothing to snipe."
        )

    embed = discord.Embed(
        description=data["content"],
        color=discord.Color.orange()
    )

    embed.set_footer(text=f"Deleted by {data['author']}")

    await interaction.response.send_message(embed=embed)


# ================= FUN COMMANDS =================
@bot.tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):

    result = random.choice(["Heads", "Tails"])

    await interaction.response.send_message(f"🪙 {result}")


@bot.tree.command(name="roll", description="Roll a dice")
async def roll(
    interaction: discord.Interaction,
    sides: int = 6
):

    if sides < 2:
        return await interaction.response.send_message(
            "❌ Dice must have at least 2 sides."
        )

    result = random.randint(1, sides)

    await interaction.response.send_message(
        f"🎲 You rolled `{result}`"
    )


@bot.tree.command(name="8ball", description="Ask the magic 8ball")
async def eightball(
    interaction: discord.Interaction,
    question: str
):

    responses = [
        "Yes",
        "No",
        "Maybe",
        "Definitely",
        "Probably not",
        "Ask again later"
    ]

    await interaction.response.send_message(
        f"🎱 {random.choice(responses)}"
    )


# ================= RPS BUTTON UI =================
class RPSView(discord.ui.View):

    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user.id

    async def play(self, interaction, choice):

        bot_choice = random.choice(
            ["rock", "paper", "scissors"]
        )

        if choice == bot_choice:
            result = "Tie!"
        elif (
            (choice == "rock" and bot_choice == "scissors") or
            (choice == "paper" and bot_choice == "rock") or
            (choice == "scissors" and bot_choice == "paper")
        ):
            result = "You win!"
        else:
            result = "You lose!"

        await interaction.response.edit_message(
            content=(
                f"You chose **{choice}**\n"
                f"Bot chose **{bot_choice}**\n\n"
                f"🏆 {result}"
            ),
            view=None
        )

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.primary)
    async def rock(self, interaction, button):
        await self.play(interaction, "rock")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.success)
    async def paper(self, interaction, button):
        await self.play(interaction, "paper")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.danger)
    async def scissors(self, interaction, button):
        await self.play(interaction, "scissors")


@bot.tree.command(name="rps", description="Play Rock Paper Scissors")
async def rps(interaction: discord.Interaction):

    await interaction.response.send_message(
        "Choose one:",
        view=RPSView(interaction.user)
    )


# ================= MODERATION =================
def is_owner(interaction):
    return interaction.user.id == OWNER_ID


@bot.tree.command(name="kick", description="Kick a member")
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if not is_owner(interaction):
        return await interaction.response.send_message(
            "❌ You are not Pax.",
            ephemeral=True
        )

    try:
        await member.kick(reason=reason)

        await interaction.response.send_message(
            f"👢 Kicked {member.mention}"
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Kick failed:\n```{e}```"
        )


@bot.tree.command(name="ban", description="Ban a member")
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if not is_owner(interaction):
        return await interaction.response.send_message(
            "❌ You are not Pax.",
            ephemeral=True
        )

    try:
        await member.ban(reason=reason)

        await interaction.response.send_message(
            f"🔨 Banned {member.mention}"
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Ban failed:\n```{e}```"
        )


@bot.tree.command(name="mute", description="Timeout a member")
async def mute(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int
):

    if not is_owner(interaction):
        return await interaction.response.send_message(
            "❌ You are not Pax.",
            ephemeral=True
        )

    try:
        until = discord.utils.utcnow() + timedelta(minutes=minutes)

        await member.timeout(until)

        await interaction.response.send_message(
            f"🔇 Muted {member.mention} for {minutes} minute(s)"
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Mute failed:\n```{e}```"
        )


# ================= RUN BOT =================
bot.run(TOKEN)
