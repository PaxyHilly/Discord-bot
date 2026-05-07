import discord
import os
from discord.ext import commands
from datetime import timedelta

# 🔐 Token from environment variable
TOKEN = os.environ['DISCORD_TOKEN']

# 👑 Only this user can use the bot
OWNER_ID = 1403449777978609674

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- OWNER ONLY CHECK ----------------
async def owner_only(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ You are not Pax.")
        return False
    return True

bot.check(owner_only)

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


# ---------------- CHANGE GAME STATUS ----------------
@bot.command()
async def setgame(ctx, *, game_name):
    await bot.change_presence(
        activity=discord.Game(name=game_name)
    )
    await ctx.send(f"🎮 Status changed to: `{game_name}`")


# ---------------- HELP COMMAND ----------------
bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Pax's Bot Commands",
        description="Prefix: `!`",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🔧 General",
        value="""
`!ping` - Check bot latency
`!hello` - Say hello
`!botname` - Bot's name
`!setgame <text>` - Change bot status
        """,
        inline=False
    )

    embed.add_field(
        name="🔨 Moderation",
        value="""
`!kick @user` - Kick a member
`!ban @user` - Ban a member
`!unban <user_id>` - Unban a member
`!mute @user <minutes>` - Timeout a member
`!unmute @user` - Remove timeout
        """,
        inline=False
    )

    embed.add_field(
        name="⚠️ Warnings",
        value="""
`!warn @user <reason>` - Warn a member
`!warnings @user` - Check warnings
        """,
        inline=False
    )

    await ctx.send(embed=embed)


# ---------------- MODERATION: KICK ----------------
@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention}")


# ---------------- MODERATION: BAN ----------------
@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention}")


# ---------------- MODERATION: UNBAN ----------------
@bot.command()
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"♻️ Unbanned {user}")


# ---------------- MODERATION: MUTE ----------------
@bot.command()
async def mute(ctx, member: discord.Member, minutes: int, *, reason=None):
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await ctx.send(f"🔇 Muted {member.mention} for {minutes} minutes")


# ---------------- MODERATION: UNMUTE ----------------
@bot.command()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 Unmuted {member.mention}")


# ---------------- WARN SYSTEM ----------------
warn_log = {}

@bot.command()
async def warn(ctx, member: discord.Member, *, reason=None):
    uid = member.id

    if uid not in warn_log:
        warn_log[uid] = []

    warn_log[uid].append(reason)

    await ctx.send(
        f"⚠️ Warned {member.mention} | Total: {len(warn_log[uid])}"
    )


@bot.command()
async def warnings(ctx, member: discord.Member):
    count = len(warn_log.get(member.id, []))
    await ctx.send(f"📄 {member.mention} has {count} warning(s).")


# ---------------- ERROR HANDLING ----------------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You are not Pax.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required arguments.")

    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")

    else:
        print(error)


bot.run(TOKEN)
