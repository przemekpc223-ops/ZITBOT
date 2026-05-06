import discord
import os
import datetime
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- KONFIGURACJA ---
# Wklej tutaj link do obrazka "OGŁOSZENIE"
IMG_URL = "LINK_DO_TWOJEGO_OBRAZKA_TUTAJ"

auto_msg_settings = {
    "text": "To jest automatyczna wiadomość ZITBOT!",
    "hour": 13,
    "minute": 0,
    "channel_id": None,
    "last_sent": None
}

@bot.event
async def on_ready():
    print(f'ZITBOT zalogowany jako {bot.user.name}')
    check_time_loop.start()
    await bot.change_presence(activity=discord.Game(name="!echo | ZITBOT"))

# --- 1. NOWA KOMENDA: ECHO (Zwykły tekst) ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def echo(ctx, *, message):
    await ctx.message.delete() # Usuwa komendę użytkownika
    await ctx.send(message)    # Wysyła czysty tekst

# --- 2. ZMODYFIKOWANY ALERT (Obrazek + Tekst) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    # Wysyła najpierw obrazek, a potem treść jako zwykłą wiadomość
    await ctx.send(IMG_URL)
    await ctx.send(f"**OGŁOSZENIE:**\n{message}")

# --- 3. USTAWIANIE AUTOWIADOMOŚCI ---
@bot.command()
@commands.has_permissions(administrator=True)
async def autowiad(ctx, czas: str, *, tresc: str):
    try:
        h, m = map(int, czas.split(':'))
        auto_msg_settings.update({"hour": h, "minute": m, "text": tresc, "channel_id": ctx.channel.id})
        await ctx.send(f"✅ Ustawiono autowiadomość o **{czas}**!")
    except:
        await ctx.send("❌ Użyj formatu: `!autowiad GG:MM treść`")

# --- 4. PĘTLA CZASOWA ---
@tasks.loop(seconds=30)
async def check_time_loop():
    now = datetime.datetime.now()
    if now.hour == auto_msg_settings["hour"] and now.minute == auto_msg_settings["minute"]:
        if auto_msg_settings["channel_id"] and auto_msg_settings["last_sent"] != now.date():
            channel = bot.get_channel(auto_msg_settings["channel_id"])
            if channel:
                await channel.send(IMG_URL) # Autowiadomość też może mieć obrazek
                await channel.send(auto_msg_settings["text"])
                auto_msg_settings["last_sent"] = now.date()

# --- 5. MODERACJA & CLEAR ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f'🗑️ Usunięto **{len(deleted)-1}** wiadomości.')
    await asyncio.sleep(5)
    await msg.delete()

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Brak"):
    await member.kick(reason=reason)
    await ctx.send(f'👢 Wyrzucono {member.mention}')

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Brak"):
    await member.ban(reason=reason)
    await ctx.send(f'🚫 Zbanowano {member.mention}')

# --- 6. POWITANIA ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel:
        await channel.send(f"Siema {member.mention}! Witamy w ekipie! 👋")

if TOKEN:
    bot.run(TOKEN)
