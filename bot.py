import discord
import os
from discord.ext import commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        # ❌ Clear all old slash commands
        bot.tree.clear_commands(guild=None)

        # ⏳ Force fresh sync
        synced = await bot.tree.sync()

        print(f"✅ RESET COMPLETE: Synced {len(synced)} commands")

    except Exception as e:
        print(f"❌ Sync error: {e}")

    print(f"Logged in as {bot.user}")


bot.run(TOKEN)
