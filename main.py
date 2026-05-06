import discord
import os
import datetime
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv

# 1. Ładowanie tokenu i podstawowa konfiguracja
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 2. Link do obrazka (Używamy linku, który podałeś)
IMG_URL = "https://media.discordapp.net/attachments/1501607488888242256/1501614691896660119/fc1139e4-b133-4dc2-a427-162457a01d95.png?ex=69fcb729&is=69fb65a9&hm=da93300966dacedb0bf51c1bf652fd14e517e54b75632c34699763207e24a69b&=&format=webp&quality=lossless&width=688&height=344"

# 3. Ustawienia autowiadomości
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
    await bot.change_presence(activity=discord.Game(name="!alert | !echo"))

# --- KOMENDY MODERACYJNE ---

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

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason="Brak"):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f'🔇 Wyciszono {member.mention} na {minutes} min.')

# --- KOMENDY INFORMACYJNE ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def echo(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    # Wysyła obrazek i treść w jednej wiadomości bez dopisku "OGŁOSZENIE"
    await ctx.send(f"{IMG_URL}\n\n{message}")

# --- SYSTEM AUTOWIADOMOŚCI ---

@bot.command()
@commands.has_permissions(administrator=True)
async def autowiad(ctx, czas: str, *, tresc: str):
    try:
        h, m = map(int, czas.split(':'))
        auto_msg_settings.update({"hour": h, "minute": m, "text": tresc, "channel_id": ctx.channel.id})
        await ctx.send(f"✅ Ustawiono autowiadomość o **{czas}** na tym kanale!")
    except:
        await ctx.send("❌ Użyj formatu: `!autowiad GG:MM treść` (np. !autowiad 15:00 Hej)")

@tasks.loop(seconds=30)
async def check_time_loop():
    now = datetime.datetime.now()
    if now.hour == auto_msg_settings["hour"] and now.minute == auto_msg_settings["minute"]:
        if auto_msg_settings["channel_id"] and auto_msg_settings["last_sent"] != now.date():
            channel = bot.get_channel(auto_msg_settings["channel_id"])
            if channel:
                # Wysyła obrazek i tekst w jednej wiadomości
                await channel.send(f"{IMG_URL}\n\n{auto_msg_settings['text']}")
                auto_msg_settings["last_sent"] = now.date()

# --- POWITANIA ---

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel:
        await channel.send(f"Siema {member.mention}! Witamy w ekipie! 👋")

# Uruchomienie
if TOKEN:
    bot.run(TOKEN)
