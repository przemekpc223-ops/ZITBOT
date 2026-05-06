import discord
import os
import datetime
import asyncio
import aiohttp
import io
import re
from discord.ext import commands, tasks
from dotenv import load_dotenv

# 1. Ładowanie tokenu
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 2. Konfiguracja Intents (KLUCZOWE!)
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  

bot = commands.Bot(command_prefix='!', intents=intents)

# --- KONFIGURACJA LINKÓW DO OBRAZKÓW ---
IMG_ALERT = "https://media.discordapp.net/attachments/1501607488888242256/1501614691896660119/fc1139e4-b133-4dc2-a427-162457a01d95.png"
IMG_WELCOME = "https://media.discordapp.net/attachments/1501607488888242256/1501618320804417617/7b93b868-fac4-4fa4-9850-f23e952874f4.png"
IMG_RULES = "https://media.discordapp.net/attachments/1501607488888242256/1501618531056488448/bddd02eb-307e-47f6-91ed-eddd1a9b2713.png"

COLORS = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "yellow": discord.Color.yellow(),
    "purple": discord.Color.purple(),
    "gold": discord.Color.gold(),
    "white": 0xFFFFFF,
    "black": 0x000000
}

auto_msg_settings = {"text": "Wiadomość automatyczna", "hour": 13, "minute": 0, "channel_id": None, "last_sent": None}

# --- FUNKCJE POMOCNICZE ---

async def send_img_as_file(target, img_url, text_content=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as resp:
            if resp.status == 200:
                data = io.BytesIO(await resp.read())
                await target.send(file=discord.File(data, 'image.png'))
                if text_content:
                    await target.send(text_content)

# --- EVENTY I ANTY-SPAM ---

@bot.event
async def on_ready():
    print(f'ZITBOT zalogowany i gotowy!')
    if not check_time_loop.is_running():
        check_time_loop.start()

@bot.event
async def on_member_join(member):
    try:
        await send_img_as_file(member, IMG_WELCOME, f"Witamy w Gwardii, **{member.name}**! Baw się dobrze!")
    except:
        pass

@bot.event
async def on_message(message):
    if message.author.bot: return

    # Anty-Link dla zwykłych graczy
    if re.search(r'http[s]?://|discord\.gg/', message.content):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            try:
                await message.author.timeout(datetime.timedelta(minutes=10), reason="Linki")
                await send_img_as_file(message.author, IMG_RULES, "Zostałeś wyciszony na 10 minut za linki!")
            except:
                pass
            return

    await bot.process_commands(message)

# --- OBSŁUGA BŁĘDÓW (To naprawi milczenie bota) ---

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ Nie masz uprawnień do komendy `{ctx.command}`!", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Musisz podać argument! (np. `!clear 10` lub `!kick @ktoś`)", delete_after=5)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Nie znaleziono takiego użytkownika.", delete_after=5)
    else:
        print(f"Błąd bota: {error}")

# --- KOMENDY MODERACYJNE ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🗑️ Usunięto **{amount}** wiadomości.")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Brak"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Wyrzucono {member.mention}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Brak"):
    await member.ban(reason=reason)
    await ctx.send(f"🚫 Zbanowano {member.mention}")

# --- KOMENDY SPECJALNE ---

@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    await send_img_as_file(ctx, IMG_ALERT, message)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def echo(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def embed(ctx, kolor: str = "blue"):
    await ctx.message.delete()
    def check(m): return m.author == ctx.author and m.channel == ctx.channel
    try:
        q1 = await ctx.send("📝 Podaj **TYTUŁ**:")
        t = await bot.wait_for('message', check=check, timeout=60)
        q2 = await ctx.send("📖 Podaj **TREŚĆ**:")
        d = await bot.wait_for('message', check=check, timeout=60)
        
        color = COLORS.get(kolor.lower(), discord.Color.blue())
        e = discord.Embed(title=t.content, description=d.content, color=color)
        e.set_footer(text=f"Admin: {ctx.author.name}")
        e.timestamp = datetime.datetime.now()
        
        await ctx.send(embed=e)
        await t.delete(); await d.delete()
    except asyncio.TimeoutError:
        await ctx.send("❌ Czas minął!")

# --- AUTOMATYKA ---

@bot.command()
@commands.has_permissions(administrator=True)
async def autowiad(ctx, czas: str, *, tresc: str):
    try:
        h, m = map(int, czas.split(':'))
        auto_msg_settings.update({"hour": h, "minute": m, "text": tresc, "channel_id": ctx.channel.id})
        await ctx.send(f"✅ Ustawiono na **{czas}**")
    except:
        await ctx.send("❌ Użyj: `!autowiad 15:00 treść`")

@tasks.loop(seconds=30)
async def check_time_loop():
    now = datetime.datetime.now()
    if now.hour == auto_msg_settings["hour"] and now.minute == auto_msg_settings["minute"]:
        if auto_msg_settings["channel_id"] and auto_msg_settings["last_sent"] != now.date():
            channel = bot.get_channel(auto_msg_settings["channel_id"])
            if channel:
                await send_img_as_file(channel, IMG_ALERT, auto_msg_settings["text"])
                auto_msg_settings["last_sent"] = now.date()

if TOKEN:
    bot.run(TOKEN)
