import discord
from discord.ext import commands
import csv
import os
import re
from datetime import datetime

# --- CONFIG ---
CSV_FILE = 'fatture.csv'
CANALE_FATTURE = 'fatture'  # Nome del canale dove gli operai scrivono
CANALE_LAVORO = 'inizio-fine-lavoro'  # ✅ NUOVO CANALE LAVORO

PREZZI = {
    '9mm': 25000,
    'sns': 14000,
    'munizioni': 25,
    'coltello': 8000,
    'mazza': 8000
}

# --- INTENTS ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# --- CREA CSV SE NON ESISTE ---
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Operaio', 'Prodotto', 'Quantita', 'Prezzo_unitario', 'Totale', 'Guadagno'])

# --- FUNZIONI ---
def pulisci_nome(nome):
    nome = nome.strip()
    nome = re.sub(r'[^\w\s]', '', nome, flags=re.UNICODE)
    return nome.lower()

def registra_vendita(operaio, prodotto, quantita):
    prezzo_unitario = PREZZI[prodotto]
    totale = prezzo_unitario * quantita
    guadagno = totale * 0.05
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([operaio, prodotto, quantita, prezzo_unitario, totale, guadagno])
    return totale, guadagno

# --- EVENTO MESSAGGI ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('/'):
        await bot.process_commands(message)
        return

    if message.channel.name == CANALE_FATTURE:
        parts = message.content.split()
        if len(parts) < 2:
            await message.channel.send("❌ Formato errato! Usa: `Nome_Operaio Prodotto Quantità`")
            return

        try:
            quantita = int(parts[-1])
        except ValueError:
            await message.channel.send("❌ Quantità non valida! Inserisci un numero.")
            return

        prodotto = parts[-2].lower()
        if prodotto not in PREZZI:
            await message.channel.send(f"❌ Prodotto non valido! Prodotti validi: {', '.join(PREZZI.keys())}")
            return

        nome_operaio_raw = ' '.join(parts[:-2])
        operaio = pulisci_nome(nome_operaio_raw)

        totale, guadagno = registra_vendita(operaio, prodotto, quantita)
        await message.channel.send(
            f"💼 **Vendita registrata!**\n"
            f"Operaio: {nome_operaio_raw}\n"
            f"Prodotto: {prodotto}\n"
            f"Quantità: {quantita}\n"
            f"Totale vendita: ${totale:,.2f}\n"
            f"Guadagno operaio: ${guadagno:,.2f}"
        )

    await bot.process_commands(message)

# --- COMANDI ---
@bot.command()
async def guadagno(ctx, *, operaio: str):
    operaio_clean = pulisci_nome(operaio)
    totale_guadagno = 0
    if not os.path.exists(CSV_FILE):
        await ctx.send("❌ Nessuna vendita registrata.")
        return
    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if pulisci_nome(row['Operaio']) == operaio_clean:
                totale_guadagno += float(row['Guadagno'])
    await ctx.send(f"💰 **Guadagno totale di {operaio}: ${totale_guadagno:,.2f}**")

@bot.command()
async def totale(ctx, *, operaio: str):
    operaio_clean = pulisci_nome(operaio)
    totale_vendite = 0
    if not os.path.exists(CSV_FILE):
        await ctx.send("❌ Nessuna vendita registrata.")
        return
    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if pulisci_nome(row['Operaio']) == operaio_clean:
                totale_vendite += float(row['Totale'])
    await ctx.send(f"💼 **Totale vendite di {operaio}: ${totale_vendite:,.2f}**")

# =========================
# 🔥 SISTEMA LAVORO
# =========================

lavoro = {}

@bot.command()
async def inizio(ctx):
    if ctx.channel.name != CANALE_LAVORO:
        await ctx.send("❌ Usa questo comando nel canale lavoro!")
        return

    user_id = str(ctx.author.id)

    if user_id in lavoro:
        await ctx.send("⚠️ Hai già iniziato a lavorare!")
        return

    lavoro[user_id] = datetime.now()

    embed = discord.Embed(
        title="🟢 INIZIO LAVORO",
        description=f"{ctx.author.mention} ha iniziato il turno",
        color=discord.Color.green()
    )

    embed.add_field(name="👤 Utente", value=ctx.author.name, inline=False)
    embed.add_field(name="🕒 Ora inizio", value=lavoro[user_id].strftime("%H:%M:%S"), inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def fine(ctx):
    if ctx.channel.name != CANALE_LAVORO:
        await ctx.send("❌ Usa questo comando nel canale lavoro!")
        return

    user_id = str(ctx.author.id)

    if user_id not in lavoro:
        await ctx.send("⚠️ Non hai iniziato a lavorare!")
        return

    inizio_time = lavoro[user_id]
    fine_time = datetime.now()

    durata = fine_time - inizio_time

    ore = durata.seconds // 3600
    minuti = (durata.seconds % 3600) // 60

    embed = discord.Embed(
        title="🔴 FINE LAVORO",
        description=f"{ctx.author.mention} ha terminato il turno",
        color=discord.Color.red()
    )

    embed.add_field(name="👤 Utente", value=ctx.author.name, inline=False)
    embed.add_field(name="🟢 Inizio", value=inizio_time.strftime("%H:%M:%S"), inline=True)
    embed.add_field(name="🔴 Fine", value=fine_time.strftime("%H:%M:%S"), inline=True)
    embed.add_field(name="⏱ Durata", value=f"{ore}h {minuti}m", inline=False)

    await ctx.send(embed=embed)

    del lavoro[user_id]

# --- AVVIO BOT ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("⚠️ Devi impostare la variabile d'ambiente DISCORD_TOKEN!")

bot.run(TOKEN)
