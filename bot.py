import discord
from discord.ext import commands
import csv
import os
import re

# CONFIG
CSV_FILE = 'fatture.csv'
CANALE_FATTURE = 'fatture'

PREZZI = {
    '9mm': 25000,
    'sns': 14000,
    'munizioni': 25
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# CREA CSV
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Operaio', 'Prodotto', 'Quantita', 'Totale'])

def pulisci(nome):
    return re.sub(r'[^\w\s]', '', nome).lower()

@bot.event
async def on_ready():
    print(f"Online come {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name == CANALE_FATTURE:
        parts = message.content.split()

        if len(parts) < 3:
            return

        nome = ' '.join(parts[:-2])
        prodotto = parts[-2].lower()
        quantita = int(parts[-1])

        if prodotto not in PREZZI:
            return

        totale = PREZZI[prodotto] * quantita

        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([pulisci(nome), prodotto, quantita, totale])

        await message.channel.send(f"💼 Salvato: {totale}")

    await bot.process_commands(message)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
