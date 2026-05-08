import discord
import os
import random
import time
import json
from datetime import timedelta
from discord.ext import commands
from openai import OpenAI

# ================= CONFIG =================
TOKEN = os.environ["DISCORD_TOKEN"]

OWNER_ID = 1403449777978609674

# ================= FILES =================
API_KEYS_FILE = "apikeys.json"
MEMORY_FILE = "memory.json"

# ================= LOAD / SAVE =================
def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# Load stored data
user_api_keys = load_json(API_KEYS_FILE)
user_memory = load_json(MEMORY_FILE)

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

# ================= MESSAGE DELETE =================
@bot.event
async def on_message_delete(message):

    if message.author.bot:
        return

    snipe_cache[message.channel.id] = {
        "content": message.content or "No text",
        "author": str(message.author)
    }

# ================= SAVE USER API KEY =================
@bot.tree.command(
    name="setkey",
    description="Save your SambaNova API key"
)
async def setkey(
    interaction: discord.Interaction,
    api_key: str
):

    user_id = str(interaction.user.id)

    user_api_keys[user_id] = api_key

    save_json(API_KEYS_FILE, user_api_keys)

    await interaction.response.send_message(
        "✅ Your API key was saved.",
        ephemeral=True
    )

# ================= CLEAR MEMORY =================
@bot.tree.command(
    name="clearmemory",
    description="Clear your AI memory"
)
async def clearmemory(interaction: discord.Interaction):

    user_id = str(interaction.user.id)

    if user_id in user_memory:
        del user_memory[user_id]

    save_json(MEMORY_FILE, user_memory)

    await interaction.response.send_message(
        "🧠 Your memory was cleared."
    )

# ================= AI COMMAND =================
@bot.tree.command(
    name="ai",
    description="Chat with AI"
)
async def ai(
    interaction: discord.Interaction,
    prompt: str
):

    await interaction.response.defer()

    user_id = str(interaction.user.id)

    # Check if user saved API key
    if user_id not in user_api_keys:

        return await interaction.followup.send(
            "❌ Use `/setkey` first to save your SambaNova API key."
        )

    api_key = user_api_keys[user_id]

    # Create AI client
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.sambanova.ai/v1"
    )

    # Create memory for user
    if user_id not in user_memory:

        user_memory[user_id] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful Discord assistant "
                    "with memory."
                )
            }
        ]

    # Add user message
    user_memory[user_id].append({
        "role": "user",
        "content": prompt
    })

    # Prevent huge memory
    if len(user_memory[user_id]) > 20:

        user_memory[user_id] = (
            [user_memory[user_id][0]] +
            user_memory[user_id][-19:]
        )

    try:

        response = client.chat.completions.create(
            model="Meta-Llama-3.3-70B-Instruct",
            messages=user_memory[user_id],
            temperature=0.7,
            max_tokens=500
        )

        reply = response.choices[0].message.content

        if not reply:
            reply = "No response."

        # Save AI reply into memory
        user_memory[user_id].append({
            "role": "assistant",
            "content": reply
        })

        # Save memory permanently
        save_json(MEMORY_FILE, user_memory)

        # Prevent Discord message limit
        if len(reply) > 1900:
            reply = reply[:1900] + "..."

        await interaction.followup.send(reply)

    except Exception as e:

        await interaction.followup.send(
            f"❌ AI error:\n```{e}```"
        )

# ================= UTILITY =================
@bot.tree.command(
    name="ping",
    description="Check bot latency"
)
async def ping(interaction: discord.Interaction):

    latency = round(bot.latency * 1000)

    await interaction.response.send_message(
        f"🏓 Pong! `{latency}ms`"
    )

@bot.tree.command(
    name="uptime",
    description="Show uptime"
)
async def uptime(interaction: discord.Interaction):

    seconds = int(time.time() - start_time)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    await interaction.response.send_message(
        f"⏱ `{hours}h {minutes}m {secs}s`"
    )

@bot.tree.command(
    name="userinfo",
    description="Get user info"
)
async def userinfo(
    interaction: discord.Interaction,
    member: discord.Member
):

    embed = discord.Embed(
        title=str(member),
        color=discord.Color.blue()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="User ID",
        value=member.id
    )

    embed.add_field(
        name="Joined",
        value=member.joined_at.strftime("%Y-%m-%d")
    )

    embed.add_field(
        name="Created",
        value=member.created_at.strftime("%Y-%m-%d")
    )

    await interaction.response.send_message(
        embed=embed
    )

@bot.tree.command(
    name="serverstats",
    description="Show server stats"
)
async def serverstats(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Members",
        value=guild.member_count
    )

    embed.add_field(
        name="Roles",
        value=len(guild.roles)
    )

    embed.add_field(
        name="Channels",
        value=len(guild.channels)
    )

    embed.add_field(
        name="Owner",
        value=str(guild.owner)
    )

    if guild.icon:
        embed.set_thumbnail(
            url=guild.icon.url
        )

    await interaction.response.send_message(
        embed=embed
    )

# ================= SNIPE =================
@bot.tree.command(
    name="snipe",
    description="Show deleted message"
)
async def snipe(interaction: discord.Interaction):

    data = snipe_cache.get(
        interaction.channel.id
    )

    if not data:

        return await interaction.response.send_message(
            "❌ Nothing to snipe."
        )

    embed = discord.Embed(
        description=data["content"],
        color=discord.Color.orange()
    )

    embed.set_footer(
        text=f"Deleted by {data['author']}"
    )

    await interaction.response.send_message(
        embed=embed
    )

# ================= FUN =================
@bot.tree.command(
    name="coinflip",
    description="Flip a coin"
)
async def coinflip(interaction: discord.Interaction):

    result = random.choice(
        ["Heads", "Tails"]
    )

    await interaction.response.send_message(
        f"🪙 {result}"
    )

@bot.tree.command(
    name="roll",
    description="Roll dice"
)
async def roll(
    interaction: discord.Interaction,
    sides: int = 6
):

    if sides < 2:

        return await interaction.response.send_message(
            "❌ Minimum is 2 sides."
        )

    result = random.randint(1, sides)

    await interaction.response.send_message(
        f"🎲 You rolled `{result}`"
    )

@bot.tree.command(
    name="8ball",
    description="Magic 8ball"
)
async def eightball(
    interaction: discord.Interaction,
    question: str
):

    responses = [
        "Yes",
        "No",
        "Maybe",
        "Definitely",
        "Ask again later",
        "Probably not"
    ]

    await interaction.response.send_message(
        f"🎱 {random.choice(responses)}"
    )

# ================= MODERATION =================
def is_owner(interaction):
    return interaction.user.id == OWNER_ID

@bot.tree.command(
    name="kick",
    description="Kick member"
)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason"
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

@bot.tree.command(
    name="ban",
    description="Ban member"
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason"
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

@bot.tree.command(
    name="mute",
    description="Timeout member"
)
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

        until = discord.utils.utcnow() + timedelta(
            minutes=minutes
        )

        await member.timeout(until)

        await interaction.response.send_message(
            f"🔇 Muted {member.mention} for {minutes} minute(s)"
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Mute failed:\n```{e}```"
        )

# ================= RUN =================
bot.run(TOKEN)
