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

# --- ROZBUDOWANA KOMENDA EMBED ---
@bot.command()
@commands.has_permissions(administrator=True)
async def embed(ctx, kolor: str = "blue"):
    # Usuwamy komendę wywołującą
    await ctx.message.delete()
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # Pytamy o Tytuł
        q1 = await ctx.send("📝 **Podaj TYTUŁ embedu:** (lub wpisz `brak`)", delete_after=60)
        msg_title = await bot.wait_for('message', check=check, timeout=60.0)
        title = msg_title.content if msg_title.content.lower() != 'brak' else None
        await msg_title.delete()
        await q1.delete()

        # Pytamy o Opis
        q2 = await ctx.send("📖 **Podaj TREŚĆ (opis) embedu:**", delete_after=60)
        msg_desc = await bot.wait_for('message', check=check, timeout=60.0)
        desc = msg_desc.content
        await msg_desc.delete()
        await q2.delete()

        # Pytamy o duży obrazek (Link)
        q3 = await ctx.send("🖼️ **Podaj LINK do dużego obrazka:** (lub wpisz `brak`)", delete_after=60)
        msg_img = await bot.wait_for('message', check=check, timeout=60.0)
        img_url = msg_img.content if msg_img.content.lower() != 'brak' else None
        await msg_img.delete()
        await q3.delete()

        # Tworzenie Embedu
        color = COLORS.get(kolor.lower(), discord.Color.blue())
        full_embed = discord.Embed(title=title, description=desc, color=color)
        
        if img_url:
            full_embed.set_image(url=img_url)
            
        full_embed.set_footer(text=f"Wysłane przez: {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        full_embed.timestamp = datetime.datetime.now()
        
        await ctx.send(embed=full_embed)

    except asyncio.TimeoutError:
        await ctx.send("❌ Czas minął! Spróbuj ponownie wpisać `!embed`.", delete_after=10)

# --- RESZTA FUNKCJI (POWITANIA, ANTY-LINK, ALERT) ---

async def send_img_as_file(target, img_url, text=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as resp:
            if resp.status == 200:
                data = io.BytesIO(await resp.read())
                await target.send(file=discord.File(data, 'image.png'))
                if text: await target.send(text)

@bot.event
async def on_message(message):
    if message.author.bot: return
    # Anty-Link
    if re.search(r'http[s]?://|discord\.gg/', message.content):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            try:
                duration = datetime.timedelta(minutes=10)
                await message.author.timeout(duration, reason="Linki")
                await send_img_as_file(message.author, IMG_RULES, "Złamałeś zasady - nie wysyłaj linków!")
            except: pass
            return
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    # Powitanie w DM
    try:
        await send_img_as_file(member, IMG_WELCOME, f"Witamy w Gwardii, **{member.name}**! Baw się dobrze.")
    except: pass

@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    await send_img_as_file(ctx, IMG_ALERT)
    await ctx.send(message)

# Uruchomienie bota
if TOKEN:
    bot.run(TOKEN)
