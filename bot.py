import discord
import os
from discord.ext import commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # 🔥 STEP 1: WIPE OLD COMMANDS (GLOBAL)
    bot.tree.clear_commands(guild=None)

    # 🔥 STEP 2: RE-SYNC EMPTY STATE FIRST
    await bot.tree.sync()

    print("🧹 Cleared all old slash commands")

    # 🔥 STEP 3: OPTIONAL — re-add a test command
    @bot.tree.command(name="ping", description="test command")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("Pong!")

    # 🔥 STEP 4: FINAL SYNC (fresh commands only)
    await bot.tree.sync()

    print("✅ Commands fully reset and synced")


bot.run(TOKEN)
