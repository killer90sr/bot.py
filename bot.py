import discord
from discord.ext import commands
import csv
import os
import re

# --- CONFIG ---
CSV_FILE = 'fatture.csv'
CANALE_FATTURE = 'fatture'  # Nome del canale dove gli operai scrivono
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
# 🧹 COMANDO PULISCI
# =========================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def pulisci(ctx, amount: int = 100):
    if amount > 100:
        amount = 100

    deleted = await ctx.channel.purge(limit=amount + 1)

    msg = await ctx.send(f"🧹 Cancellati {len(deleted)-1} messaggi")
    await msg.delete(delay=3)

# --- AVVIO BOT ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("⚠️ Devi impostare la variabile d'ambiente DISCORD_TOKEN!")
bot.run(TOKEN)
