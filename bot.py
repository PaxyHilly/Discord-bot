import discord
import os
from discord.ext import commands

TOKEN = os.environ['DISCORD_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- BASIC COMMANDS ----------------
@bot.event
async def on_ready():
    print("Pax's Bot is online!")
    await bot.change_presence(
        activity=discord.Game(name="Managing the server")
    )

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}!")

@bot.command()
async def botname(ctx):
    await ctx.send("My name is Pax's Bot 😎")

# ---------------- MODERATION: KICK ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention}")

# ---------------- MODERATION: BAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention}")

# ---------------- MODERATION: UNBAN ----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"♻️ Unbanned {user}")

# ---------------- MODERATION: TIMEOUT (MUTE) ----------------
@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason=None):
    until = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await ctx.send(f"🔇 Muted {member.mention} for {minutes} minutes")

# ---------------- MODERATION: UNMUTE ----------------
@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 Unmuted {member.mention}")

# ---------------- WARN SYSTEM ----------------
warn_log = {}

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    uid = member.id
    if uid not in warn_log:
        warn_log[uid] = []
    warn_log[uid].append(reason)
    await ctx.send(f"⚠️ Warned {member.mention} | Total: {len(warn_log[uid])}")

@bot.command()
async def warnings(ctx, member: discord.Member):
    count = len(warn_log.get(member.id, []))
    await ctx.send(f"📄 {member.mention} has {count} warning(s).")

# ---------------- ERROR HANDLING ----------------
@kick.error
@ban.error
@mute.error
@warn.error
async def perms_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")

bot.run(TOKEN)
