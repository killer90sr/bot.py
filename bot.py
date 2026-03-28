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
CANALE_LOG = 'log-lavoro'

PREZZI = {
    '9mm': 25000,
    'sns': 14000,
    'munizioni': 25,
    'coltello': 8000,
    'mazza': 8000
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# --- CREA CSV ---
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Operaio', 'Prodotto', 'Quantita', 'Totale', 'Guadagno'])

# --- FUNZIONI ---
def pulisci_nome(nome):
    return re.sub(r'[^\w\s]', '', nome).lower()

def registra_vendita(operaio, prodotto, quantita):
    prezzo = PREZZI[prodotto]
    totale = prezzo * quantita
    guadagno = totale * 0.05

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([operaio, prodotto, quantita, totale, guadagno])

    return totale, guadagno

# --- EVENTO MESSAGGI ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name == CANALE_FATTURE:
        parts = message.content.split()

        if len(parts) < 3:
            return

        try:
            quantita = int(parts[-1])
        except:
            return

        prodotto = parts[-2].lower()
        if prodotto not in PREZZI:
            await message.channel.send("❌ Prodotto non valido!")
            return

        nome = ' '.join(parts[:-2])
        operaio = pulisci_nome(nome)

        totale, guadagno = registra_vendita(operaio, prodotto, quantita)

        await message.channel.send(
            f"💼 Vendita registrata!\n"
            f"Operaio: {nome}\n"
            f"Prodotto: {prodotto}\n"
            f"Quantità: {quantita}\n"
            f"Totale: ${totale:,.2f}\n"
            f"Guadagno: ${guadagno:,.2f}"
        )

    await bot.process_commands(message)

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

        # ❌ niente messaggi nel canale
        await interaction.response.defer()

        # ✅ log
        for channel in interaction.guild.text_channels:
            if channel.name == CANALE_LOG:
                await channel.send(
                    f"🟢 {interaction.user.mention} ha iniziato alle {lavoro[user_id].strftime('%H:%M:%S')}"
                )

    @discord.ui.button(label="🔴 Fine Lavoro", style=discord.ButtonStyle.red)
    async def fine(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        if user_id not in lavoro:
            await interaction.response.send_message("⚠️ Non hai iniziato!", ephemeral=True)
            return

        start = lavoro[user_id]
        end = datetime.now()
        durata = end - start

        ore = durata.seconds // 3600
        minuti = (durata.seconds % 3600) // 60

        # ❌ niente messaggi nel canale
        await interaction.response.defer()

        # ✅ log
        for channel in interaction.guild.text_channels:
            if channel.name == CANALE_LOG:
                await channel.send(
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

                trovato = False

                async for msg in channel.history(limit=20):
                    if msg.author == bot.user:
                        trovato = True
                        break

                if trovato:
                    continue

                embed = discord.Embed(
                    title="📋 TIMBRATURA LAVORO",
                    description="Clicca i bottoni sotto",
                    color=discord.Color.blue()
                )

                await channel.send(embed=embed, view=LavoroView())
                print("Pannello creato!")

# --- COMANDO GUADAGNO ---
@bot.command()
async def guadagno(ctx, *, operaio: str):
    if ctx.channel.name != "totale-fatture":
        return

    operaio = pulisci_nome(operaio)
    totale = 0

    if not os.path.exists(CSV_FILE):
        await ctx.send("❌ Nessuna vendita.")
        return

    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if pulisci_nome(row[0]) == operaio:
                totale += float(row[4])

    await ctx.send(f"💰 Guadagno totale: ${totale:,.2f}")

# --- AVVIO ---
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
