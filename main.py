import discord
import os
import datetime
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Ładowanie tokenu
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Konfiguracja uprawnień
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- ZMIENNE DLA AUTOWIADOMOŚCI ---
# Domyślnie ustawione na 13:00, ale brat może to zmienić komendą
auto_msg_settings = {
    "text": "To jest automatyczna wiadomość ZITBOT!",
    "hour": 13,
    "minute": 0,
    "channel_id": None,
    "last_sent": None
}

@bot.event
async def on_ready():
    print(f'ZITBOT zalogowany i gotowy jako {bot.user.name}')
    check_time_loop.start() # Uruchamia sprawdzanie godziny
    await bot.change_presence(activity=discord.Game(name="!autowiad | ZITBOT"))

# --- 1. KOMENDA: USTAWIANIE AUTOWIADOMOŚCI ---
# Użycie: !autowiad 13:00 Treść wiadomości
@bot.command()
@commands.has_permissions(administrator=True)
async def autowiad(ctx, czas: str, *, tresc: str):
    try:
        # Rozdzielamy godzinę i minutę (format GG:MM)
        h, m = map(int, czas.split(':'))
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError
        
        auto_msg_settings["hour"] = h
        auto_msg_settings["minute"] = m
        auto_msg_settings["text"] = tresc
        auto_msg_settings["channel_id"] = ctx.channel.id
        
        await ctx.send(f"✅ **ZITBOT Konfiguracja:**\nCodziennie o **{czas}** wyślę: \"{tresc}\" na tym kanale.")
    except:
        await ctx.send("❌ **Błąd!** Użyj formatu: `!autowiad GG:MM treść` (np. `!autowiad 13:30 Cześć!`) ")

# --- 2. PĘTLA: WYSYŁANIE O WYBRANEJ GODZINIE ---
@tasks.loop(seconds=30)
async def check_time_loop():
    now = datetime.datetime.now()
    # Jeśli godzina i minuta się zgadzają ORAZ nie wysłaliśmy tego dzisiaj
    if now.hour == auto_msg_settings["hour"] and now.minute == auto_msg_settings["minute"]:
        if auto_msg_settings["channel_id"] and auto_msg_settings["last_sent"] != now.date():
            channel = bot.get_channel(auto_msg_settings["channel_id"])
            if channel:
                embed = discord.Embed(
                    title="🕒 Automatyczne Przypomnienie",
                    description=auto_msg_settings["text"],
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow()
                )
                await channel.send(embed=embed)
                auto_msg_settings["last_sent"] = now.date() # Zapisuje, że wysłano dzisiaj

# --- 3. KOMENDA: CZYSZCZENIE CZATU (CLEAR) ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount < 1:
        await ctx.send("Podaj liczbę większą od 0!")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f'🗑️ Usunięto **{len(deleted)-1}** wiadomości.')
    await asyncio.sleep(5)
    await msg.delete()

# --- 4. POWITANIA ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel:
        await channel.send(f"Siema {member.mention}! Witamy na serwerze! ZITBOT Cię widzi! 👋")

# --- 5. MODERACJA ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Brak powodu"):
    await member.kick(reason=reason)
    await ctx.send(f'👢 Wyrzucono {member.mention}. Powód: {reason}')

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Brak powodu"):
    await member.ban(reason=reason)
    await ctx.send(f'🚫 Zbanowano {member.mention}. Powód: {reason}')

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason="Brak powodu"):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f'🔇 Wyciszono {member.mention} na {minutes} min. Powód: {reason}')

# --- 6. ALERTY (OGŁOSZENIA) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    embed = discord.Embed(title="📢 OGŁOSZENIE ZITBOT", description=message, color=discord.Color.red())
    embed.set_footer(text=f"Admin: {ctx.author}")
    await ctx.send(embed=embed)

# Uruchomienie bota
if TOKEN:
    bot.run(TOKEN)
else:
    print("BŁĄD: Brak DISCORD_TOKEN w zmiennych środowiskowych!")
