import discord
import os
import datetime
import asyncio
import aiohttp
import io
import re
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- KONFIGURACJA LINKÓW DO OBRAZKÓW ---
IMG_ALERT = "https://media.discordapp.net/attachments/1501607488888242256/1501614691896660119/fc1139e4-b133-4dc2-a427-162457a01d95.png?ex=69fcb729&is=69fb65a9&hm=da93300966dacedb0bf51c1bf652fd14e517e54b75632c34699763207e24a69b&=&format=webp&quality=lossless&width=688&height=344"
IMG_WELCOME = "https://media.discordapp.net/attachments/1501607488888242256/1501618320804417617/7b93b868-fac4-4fa4-9850-f23e952874f4.png?ex=69fcba8a&is=69fb690a&hm=93c9f2f0a7b5e550cb4ca2f78e45a0e1bcfc7dea70a0e3074cc9c471b67b2360&=&format=webp&quality=lossless&width=656&height=438"
IMG_RULES = "https://media.discordapp.net/attachments/1501607488888242256/1501618531056488448/bddd02eb-307e-47f6-91ed-eddd1a9b2713.png?ex=69fcbabc&is=69fb693c&hm=1d51ad13bcba9114c03eaf7b170a7a42a53b81893692b390b0beb20db0a4d158&=&format=webp&quality=lossless&width=1230&height=820"

# --- USTAWIENIA AUTOWIADOMOŚCI ---
auto_msg_settings = {"text": "Wiadomość automatyczna", "hour": 13, "minute": 0, "channel_id": None, "last_sent": None}

# Funkcja pomocnicza do wysyłania obrazka z linku jako pliku
async def send_img_as_file(target, img_url, text=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as resp:
            if resp.status == 200:
                data = io.BytesIO(await resp.read())
                await target.send(file=discord.File(data, 'image.png'))
                if text: await target.send(text)

@bot.event
async def on_ready():
    print(f'ZITBOT zalogowany!')
    check_time_loop.start()

# --- 1. SYSTEM ANTY-LINK (Anty-Spam) ---
@bot.event
async def on_message(message):
    if message.author.bot: return

    # Szukamy linków w wiadomości
    if re.search(r'http[s]?://|discord\.gg/', message.content):
        if not message.author.guild_permissions.manage_messages: # Admini mogą wysyłać linki
            await message.delete()
            
            # Dajemy przerwę (timeout) na 10 minut
            try:
                duration = datetime.timedelta(minutes=10)
                await message.author.timeout(duration, reason="Spamowanie linkami")
            except: pass # Jeśli bot nie ma uprawnień do timeoutu

            # Wysyłamy upomnienie w DM z obrazkiem "Zasady"
            try:
                await send_img_as_file(message.author, IMG_RULES, "Zostałeś wyciszony na 10 minut za wysyłanie linków. Przeczytaj zasady!")
            except: pass
            return

    await bot.process_commands(message)

# --- 2. POWITANIE W DM PO WEJŚCIU ---
@bot.event
async def on_member_join(member):
    # Link do zaproszenia (możesz zmienić na stały link swojego serwera)
    invite_link = "https://discord.gg/TWOJ-LINK" 
    
    try:
        # Wysyła obrazek i tekst w DM (prywatna wiadomość)
        await send_img_as_file(member, IMG_WELCOME, f"Witamy w Gwardii! Baw się dobrze na naszym serwerze!\nLink do serwera: {invite_link}")
    except:
        print(f"Nie udało się wysłać DM do {member.name}")

# --- KOMENDA ALERT (Zdjęcie i tekst osobno) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    await send_img_as_file(ctx, IMG_ALERT)
    await ctx.send(message)

# --- SYSTEM AUTOWIADOMOŚCI ---
@bot.command()
@commands.has_permissions(administrator=True)
async def autowiad(ctx, czas: str, *, tresc: str):
    try:
        h, m = map(int, czas.split(':'))
        auto_msg_settings.update({"hour": h, "minute": m, "text": tresc, "channel_id": ctx.channel.id})
        await ctx.send(f"✅ Ustawiono autowiadomość o {czas}!")
    except:
        await ctx.send("❌ Użyj: `!autowiad 15:00 wiadomość`")

@tasks.loop(seconds=30)
async def check_time_loop():
    now = datetime.datetime.now()
    if now.hour == auto_msg_settings["hour"] and now.minute == auto_msg_settings["minute"]:
        if auto_msg_settings["channel_id"] and auto_msg_settings["last_sent"] != now.date():
            channel = bot.get_channel(auto_msg_settings["channel_id"])
            if channel:
                await send_img_as_file(channel, IMG_ALERT)
                await channel.send(auto_msg_settings["text"])
                auto_msg_settings["last_sent"] = now.date()

# --- MODERACJA ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)

if TOKEN:
    bot.run(TOKEN)
