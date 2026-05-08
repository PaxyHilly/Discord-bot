import discord
import os
import json
import time
from discord.ext import commands
from openai import OpenAI

# ================= CONFIG =================
TOKEN = os.environ["DISCORD_TOKEN"]

# YOUR SERVER ID
GUILD_ID = 1476207834306973766

# ================= FILES =================
API_KEYS_FILE = "apikeys.json"
MEMORY_FILE = "memory.json"
MODELS_FILE = "models.json"
NAMES_FILE = "names.json"
PERSONAS_FILE = "personas.json"

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
user_names = load_json(NAMES_FILE)
user_personas = load_json(PERSONAS_FILE)

# ================= BOT =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

start_time = time.time()

# ================= SPLIT =================
def split_message(text, limit=2000):
    return [
        text[i:i + limit]
        for i in range(0, len(text), limit)
    ]

# ================= READY =================
@bot.event
async def on_ready():

    try:

        guild = discord.Object(id=GUILD_ID)

        bot.tree.clear_commands(guild=guild)

        synced = await bot.tree.sync(guild=guild)

        print(f"✅ Synced {len(synced)} guild commands")

    except Exception as e:
        print(f"❌ Sync error: {e}")

    print(f"🤖 Logged in as {bot.user}")

# ================= MODEL UI =================
class ModelSelect(discord.ui.View):

    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = str(user_id)

    @discord.ui.select(
        placeholder="Choose AI model...",
        options=[

            discord.SelectOption(
                label="Llama 3.3 (Recommended)",
                value="Meta-Llama-3.3-70B-Instruct"
            ),

            discord.SelectOption(
                label="Llama 3.1 (Old)",
                value="Meta-Llama-3.1-405B-Instruct"
            ),

            discord.SelectOption(
                label="Qwen 2.5 (Fast)",
                value="Qwen2.5-72B-Instruct"
            ),

            discord.SelectOption(
                label="DeepSeek R1",
                value="DeepSeek-R1"
            ),
        ]
    )
    async def select_callback(
        self,
        interaction: discord.Interaction,
        select
    ):

        user_models[self.user_id] = select.values[0]

        save_json(MODELS_FILE, user_models)

        await interaction.response.edit_message(
            content=f"✅ Model set to `{select.values[0]}`",
            view=None
        )

# ================= COMMANDS =================

# ===== MODEL =====
@bot.tree.command(
    name="model",
    description="Choose AI model",
    guild=discord.Object(id=GUILD_ID)
)
async def model(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🧠 Choose your AI model:",
        view=ModelSelect(interaction.user.id),
        ephemeral=True
    )

# ===== SETKEY =====
@bot.tree.command(
    name="setkey",
    description="Save API key",
    guild=discord.Object(id=GUILD_ID)
)
async def setkey(
    interaction: discord.Interaction,
    api_key: str
):

    try:

        user_api_keys[str(interaction.user.id)] = api_key

        save_json(API_KEYS_FILE, user_api_keys)

        await interaction.response.send_message(
            "✅ API key saved successfully.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"❌ Failed to save key:\n```{e}```",
            ephemeral=True
        )

# ===== SETNAME =====
@bot.tree.command(
    name="setname",
    description="Set AI name",
    guild=discord.Object(id=GUILD_ID)
)
async def setname(
    interaction: discord.Interaction,
    name: str
):

    user_names[str(interaction.user.id)] = name

    save_json(NAMES_FILE, user_names)

    await interaction.response.send_message(
        f"✅ AI name set to `{name}`",
        ephemeral=True
    )

# ===== SETPERSONA =====
@bot.tree.command(
    name="setpersona",
    description="Set AI personality",
    guild=discord.Object(id=GUILD_ID)
)
async def setpersona(
    interaction: discord.Interaction,
    persona: str
):

    user_personas[str(interaction.user.id)] = persona

    save_json(PERSONAS_FILE, user_personas)

    await interaction.response.send_message(
        "🎭 Personality updated.",
        ephemeral=True
    )

# ===== CLEAR MEMORY =====
@bot.tree.command(
    name="clearmemory",
    description="Clear AI memory",
    guild=discord.Object(id=GUILD_ID)
)
async def clearmemory(
    interaction: discord.Interaction
):

    uid = str(interaction.user.id)

    if uid in user_memory:
        del user_memory[uid]

    save_json(MEMORY_FILE, user_memory)

    await interaction.response.send_message(
        "🧠 Memory cleared."
    )

# ===== AI =====
@bot.tree.command(
    name="ai",
    description="Talk to AI",
    guild=discord.Object(id=GUILD_ID)
)
async def ai(
    interaction: discord.Interaction,
    prompt: str
):

    await interaction.response.defer()

    user_id = str(interaction.user.id)

    if user_id not in user_api_keys:

        return await interaction.followup.send(
            "❌ Use `/setkey` first."
        )

    client = OpenAI(
        api_key=user_api_keys[user_id],
        base_url="https://api.sambanova.ai/v1"
    )

    model = user_models.get(
        user_id,
        "Meta-Llama-3.3-70B-Instruct"
    )

    # ===== MEMORY =====
    if user_id not in user_memory:
        user_memory[user_id] = []

    system_prompt = {
        "role": "system",
        "content": (
            f"You are an AI assistant.\n"
            f"Name: {user_names.get(user_id, 'Assistant')}.\n"
            f"Personality: {user_personas.get(user_id, 'helpful, friendly')}.\n"
            f"You are chatting inside Discord."
        )
    }

    if not user_memory[user_id]:

        user_memory[user_id].append(system_prompt)

    elif user_memory[user_id][0]["role"] != "system":

        user_memory[user_id].insert(0, system_prompt)

    user_memory[user_id].append({
        "role": "user",
        "content": prompt
    })

    # limit memory
    if len(user_memory[user_id]) > 20:

        user_memory[user_id] = (
            [user_memory[user_id][0]] +
            user_memory[user_id][-19:]
        )

    try:

        response = client.chat.completions.create(
            model=model,
            messages=user_memory[user_id],
            temperature=0.7,
            max_tokens=500
        )

        reply = (
            response.choices[0].message.content
            or
            "No response."
        )

        user_memory[user_id].append({
            "role": "assistant",
            "content": reply
        })

        save_json(MEMORY_FILE, user_memory)

        chunks = split_message(reply)

        for chunk in chunks:

            await interaction.followup.send(chunk)

    except Exception as e:

        await interaction.followup.send(
            f"❌ AI error:\n```{e}```"
        )

# ===== PING =====
@bot.tree.command(
    name="ping",
    description="Check latency",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        f"🏓 {round(bot.latency * 1000)}ms"
    )

# ===== UPTIME =====
@bot.tree.command(
    name="uptime",
    description="Bot uptime",
    guild=discord.Object(id=GUILD_ID)
)
async def uptime(
    interaction: discord.Interaction
):

    seconds = int(time.time() - start_time)

    await interaction.response.send_message(
        f"⏱ {seconds} seconds"
    )

# ================= RUN =================
bot.run(TOKEN)
