import discord
from discord.ext import commands
import csv
import os
import re
from datetime import datetime

# --- CONFIG ---
CSV_FILE = 'fatture.csv'
CANALE_FATTURE = 'fatture'
CANALE_LAVORO = 'inizio-fine-lavoro'

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

# --- CREA CSV ---
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
            await message.channel.send("❌ Quantità non valida!")
            return

        prodotto = parts[-2].lower()
        if prodotto not in PREZZI:
            await message.channel.send(f"❌ Prodotto non valido!")
            return

        nome_operaio_raw = ' '.join(parts[:-2])
        operaio = pulisci_nome(nome_operaio_raw)

        totale, guadagno = registra_vendita(operaio, prodotto, quantita)
        await message.channel.send(
            f"💼 **Vendita registrata!**\n"
            f"Operaio: {nome_operaio_raw}\n"
            f"Totale: ${totale:,.2f}\n"
            f"Guadagno: ${guadagno:,.2f}"
        )

    await bot.process_commands(message)

# --- COMANDI ---
@bot.command()
async def guadagno(ctx, *, operaio: str):
    operaio_clean = pulisci_nome(operaio)
    totale_guadagno = 0

    if not os.path.exists(CSV_FILE):
        await ctx.send("❌ Nessuna vendita.")
        return

    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if pulisci_nome(row['Operaio']) == operaio_clean:
                totale_guadagno += float(row['Guadagno'])

    await ctx.send(f"💰 Guadagno: ${totale_guadagno:,.2f}")

@bot.command()
async def totale(ctx, *, operaio: str):
    operaio_clean = pulisci_nome(operaio)
    totale_vendite = 0

    if not os.path.exists(CSV_FILE):
        await ctx.send("❌ Nessuna vendita.")
        return

    with open(CSV_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if pulisci_nome(row['Operaio']) == operaio_clean:
                totale_vendite += float(row['Totale'])

    await ctx.send(f"💼 Totale: ${totale_vendite:,.2f}")

# =========================
# 🔥 SISTEMA LAVORO
# =========================

lavoro = {}

class LavoroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Inizio Lavoro", style=discord.ButtonStyle.green)
    async def inizio(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        if user_id in lavoro:
            await interaction.response.send_message("⚠️ Hai già iniziato!", ephemeral=True)
            return

        lavoro[user_id] = datetime.now()

        await interaction.response.send_message(
            f"🟢 {interaction.user.mention} ha iniziato alle {lavoro[user_id].strftime('%H:%M:%S')}"
        )

    @discord.ui.button(label="🔴 Fine Lavoro", style=discord.ButtonStyle.red)
    async def fine(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        if user_id not in lavoro:
            await interaction.response.send_message("⚠️ Non hai iniziato!", ephemeral=True)
            return

        inizio = lavoro[user_id]
        fine = datetime.now()
        durata = fine - inizio

        ore = durata.seconds // 3600
        minuti = (durata.seconds % 3600) // 60

        await interaction.response.send_message(
            f"🔴 {interaction.user.mention} ha finito\n⏱ {ore}h {minuti}m"
        )

        del lavoro[user_id]

# --- PANNELLO AUTOMATICO ---
@bot.event
async def on_ready():
    print(f"Online come {bot.user}")

    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name == CANALE_LAVORO:

                # controlla se già esiste
                async for msg in channel.history(limit=20):
                    if msg.author == bot.user:
                        return

                embed = discord.Embed(
                    title="📋 TIMBRATURA LAVORO",
                    description="Clicca i bottoni sotto",
                    color=discord.Color.blue()
                )

                await channel.send(embed=embed, view=LavoroView())
                print("Pannello creato!")

# --- AVVIO ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("⚠️ Devi impostare il token!")

bot.run(TOKEN)
