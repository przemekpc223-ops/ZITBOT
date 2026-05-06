import discord
import os
import datetime
from discord.ext import commands
from dotenv import load_dotenv

# Wczytywanie tokenu (lokalnie z .env, na Railway ze zmiennych Variables)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Konfiguracja uprawnień (Intents)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'ZITBOT zalogowany jako {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="!help | ZITBOT"))

# --- 1. POWITANIA ---
@bot.event
async def on_member_join(member):
    # Szuka kanału o nazwie 'powitania'
    channel = discord.utils.get(member.guild.text_channels, name="powitania")
    if channel:
        await channel.send(f"Siema {member.mention}! Witamy na serwerze! ZITBOT jest z Tobą! 👋")

# --- 2. WYRZUCANIE (KICK) ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Brak powodu"):
    try:
        await member.kick(reason=reason)
        await ctx.send(f'👢 Wyrzucono {member.mention}. Powód: {reason}')
    except Exception as e:
        await ctx.send(f'❌ Błąd: {e}')

# --- 3. BANOWANIE ---
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Brak powodu"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f'🚫 Zbanowano na stałe {member.mention}. Powód: {reason}')
    except Exception as e:
        await ctx.send(f'❌ Błąd: {e}')

# --- 4. MUTOWANIE (Timeout) ---
@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason="Brak powodu"):
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f'🔇 {member.mention} wyciszony na {minutes} minut. Powód: {reason}')
    except Exception as e:
        await ctx.send(f'❌ Błąd: {e}')

# --- 5. ALERTY (Ogłoszenia) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def alert(ctx, *, message):
    await ctx.message.delete()
    embed = discord.Embed(
        title="📢 OGŁOSZENIE ZITBOT",
        description=message,
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"Wysłano przez: {ctx.author}")
    await ctx.send(embed=embed)

# Start bota
if TOKEN:
    bot.run(TOKEN)
else:
    print("BŁĄD: Brak DISCORD_TOKEN!")
