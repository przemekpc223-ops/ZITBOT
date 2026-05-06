import discord
import os
import datetime
import asyncio
import aiohttp
import io
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Link do Twojego obrazka
IMG_URL = "https://media.discordapp.net/attachments/1501607488888242256/1501614691896660119/fc1139e4-b133-4dc2-a427-162457a01d95.png?ex=69fcb729&is=69fb65a9&hm=da93300966dacedb0bf51c1bf652fd14e517e54b75632c34699763207e24a69b&=&format=webp&quality=lossless&width=688&height=344"

auto_msg_settings = {
    "text": "To jest automatyczna wiadomość ZITBOT!",
    "hour": 13,
    "minute": 0,
    "channel_id": None,
    "last_sent": None
}

# --- FUNKCJA WYSYŁAJĄCA DWIE OSOBNE WIADOMOŚCI ---
async def send_separate_alert(target, text_content):
    async with aiohttp.ClientSession() as session:
        async with session.get(IMG_URL) as resp:
            if resp.status == 200:
                data = io.BytesIO(await resp.read())
                # WIADOMOŚĆ 1: Sam plik obrazu
                await target.send(file=discord.File(data, 'ogloszenie.png'))
                # WIADOMOŚĆ 2: Sam tekst (osobny dymek)
                await target.send(text_content)
            else:
                await target.send("Błąd: Nie udało się pobrać obrazka.")

@bot.event
async def on_ready():
    print(f'ZITBOT gotowy! Wysyła obrazek i tekst jako osobne posty.')
    check_time_loop.start()

# --- 1. ALERT (Dwa osobne dymki) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    await send_separate_alert(ctx, message)

# --- 2. ECHO ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def echo(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

# --- 3. AUTOWIADOMOŚĆ ---
@bot.command()
@commands.has_permissions(administrator=True)
async def autowiad(ctx, czas: str, *, tresc: str):
    try:
        h, m = map(int, czas.split(':'))
        auto_msg_settings.update({"hour": h, "minute": m, "text": tresc, "channel_id": ctx.channel.id})
        await ctx.send(f"✅ Ustawiono! Obrazek i tekst pojawią się osobno o **{czas}**.")
    except:
        await ctx.send("❌ Użyj formatu: `!autowiad 15:00 wiadomość`.")

@tasks.loop(seconds=30)
async def check_time_loop():
    now = datetime.datetime.now()
    if now.hour == auto_msg_settings["hour"] and now.minute == auto_msg_settings["minute"]:
        if auto_msg_settings["channel_id"] and auto_msg_settings["last_sent"] != now.date():
            channel = bot.get_channel(auto_msg_settings["channel_id"])
            if channel:
                await send_separate_alert(channel, auto_msg_settings["text"])
                auto_msg_settings["last_sent"] = now.date()

# --- MODERACJA ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f'🗑️ Usunięto **{len(deleted)-1}** wiadomości.')
    await asyncio.sleep(5)
    await msg.delete()

if TOKEN:
    bot.run(TOKEN)
