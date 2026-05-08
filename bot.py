import discord
import os
import random
import time
import json
import asyncio
from discord.ext import commands
from openai import OpenAI

# ================= CONFIG =================
TOKEN = os.environ["DISCORD_TOKEN"]
OWNER_ID = 1403449777978609674

# ================= FILES =================
API_KEYS_FILE = "apikeys.json"
MEMORY_FILE = "memory.json"
MODELS_FILE = "models.json"

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

user_api_keys = load_json(API_KEYS_FILE)
user_memory = load_json(MEMORY_FILE)
user_models = load_json(MODELS_FILE)

# ================= SPLIT =================
def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

# ================= BOT =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

snipe_cache = {}
start_time = time.time()

# ================= READY =================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    print(f"🤖 Logged in as {bot.user}")

# ================= SNIPE =================
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    snipe_cache[message.channel.id] = {
        "content": message.content or "No text",
        "author": str(message.author)
    }

# ================= MODEL UI =================
class ModelSelect(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = str(user_id)

    @discord.ui.select(
        placeholder="Choose AI model...",
        options=[
            discord.SelectOption(label="Llama 3.3 (Recommended)", value="Meta-Llama-3.3-70B-Instruct"),
            discord.SelectOption(label="Llama 3.1 (Old)", value="Meta-Llama-3.1-405B-Instruct"),
            discord.SelectOption(label="Qwen 2.5 (Fast)", value="Qwen2.5-72B-Instruct"),
            discord.SelectOption(label="DeepSeek R1", value="DeepSeek-R1"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select):

        user_models[self.user_id] = select.values[0]
        save_json(MODELS_FILE, user_models)

        await interaction.response.edit_message(
            content=f"✅ Model set to `{select.values[0]}`",
            view=None
        )

# ================= MODEL COMMAND =================
@bot.tree.command(name="model")
async def model(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🧠 Choose AI model:",
        view=ModelSelect(interaction.user.id),
        ephemeral=True
    )

# ================= SET KEY =================
@bot.tree.command(name="setkey")
async def setkey(interaction: discord.Interaction, api_key: str):

    user_api_keys[str(interaction.user.id)] = api_key
    save_json(API_KEYS_FILE, user_api_keys)

    await interaction.response.send_message("✅ API key saved.", ephemeral=True)

# ================= CLEAR MEMORY =================
@bot.tree.command(name="clearmemory")
async def clearmemory(interaction: discord.Interaction):

    uid = str(interaction.user.id)

    if uid in user_memory:
        del user_memory[uid]

    save_json(MEMORY_FILE, user_memory)

    await interaction.response.send_message("🧠 Memory cleared.")

# ================= AI COMMAND =================
@bot.tree.command(name="ai")
async def ai(interaction: discord.Interaction, prompt: str):

    await interaction.response.defer()

    user_id = str(interaction.user.id)

    if user_id not in user_api_keys:
        return await interaction.followup.send("❌ Use `/setkey` first.")

    client = OpenAI(
        api_key=user_api_keys[user_id],
        base_url="https://api.sambanova.ai/v1"
    )

    model = user_models.get(
        user_id,
        "Meta-Llama-3.3-70B-Instruct"
    )

    if user_id not in user_memory:
        user_memory[user_id] = [
            {
                "role": "system",
                "content": "You are a helpful Discord assistant with memory."
            }
        ]

    user_memory[user_id].append({
        "role": "user",
        "content": prompt
    })

    if len(user_memory[user_id]) > 20:
        user_memory[user_id] = [
            user_memory[user_id][0]
        ] + user_memory[user_id][-19:]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=user_memory[user_id],
            temperature=0.7,
            max_tokens=500
        )

        reply = response.choices[0].message.content or "No response."

        user_memory[user_id].append({
            "role": "assistant",
            "content": reply
        })

        save_json(MEMORY_FILE, user_memory)

        # ================= FIXED SENDING =================
        channel = interaction.channel
        chunks = split_message(reply)

        for chunk in chunks:
            try:
                await channel.send(chunk)
                await asyncio.sleep(0.25)
            except Exception as e:
                print(f"Send error: {e}")

    except Exception as e:
        await interaction.followup.send(f"❌ AI error:\n```{e}```")

# ================= UTILS =================
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms")

@bot.tree.command(name="uptime")
async def uptime(interaction: discord.Interaction):
    seconds = int(time.time() - start_time)
    await interaction.response.send_message(f"⏱ {seconds}s")

# ================= SNIPE =================
@bot.tree.command(name="snipe")
async def snipe(interaction: discord.Interaction):

    data = snipe_cache.get(interaction.channel.id)

    if not data:
        return await interaction.response.send_message("Nothing to snipe.")

    embed = discord.Embed(description=data["content"])
    embed.set_footer(text=data["author"])

    await interaction.response.send_message(embed=embed)

# ================= RUN BOT =================
bot.run(TOKEN)
