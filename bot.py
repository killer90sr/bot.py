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
            await message.channel.send("❌ Formato errato!")
            return

        try:
            quantita = int(parts[-1])
        except ValueError:
            await message.channel.send("❌ Quantità non valida!")
            return

        prodotto = parts[-2].lower()
        if prodotto not in PREZZI:
            await message.channel.send("❌ Prodotto non valido!")
            return

        nome_operaio_raw = ' '.join(parts[:-2])
        operaio = pulisci_nome(nome_operaio_raw)

        totale, guadagno = registra_vendita(operaio, prodotto, quantita)
        await message.channel.send(
            f"💼 Vendita registrata!\nTotale: ${totale:,.2f}\nGuadagno: ${guadagno:,.2f}"
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
# 🧹 PULISCI
# =========================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def pulisci(ctx, amount: int = 100):
    if amount > 100:
        amount = 100

    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Cancellati {len(deleted)-1} messaggi")
    await msg.delete(delay=3)

# =========================
# 🔥 LAVORO CON BOTTONI
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

        await interaction.response.send_message("✅ Turno iniziato!", ephemeral=True)

        log = discord.utils.get(interaction.guild.text_channels, name=CANALE_LOG)
        if log:
            await log.send(f"🟢 {interaction.user} ha iniziato alle {lavoro[user_id].strftime('%H:%M:%S')}")

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

        await interaction.response.send_message("✅ Turno finito!", ephemeral=True)

        log = discord.utils.get(interaction.guild.text_channels, name=CANALE_LOG)
        if log:
            await log.send(f"🔴 {interaction.user} ha finito\n⏱ {ore}h {minuti}m")

        del lavoro[user_id]

# =========================
# 📋 COMANDO PANNELLO
# =========================
@bot.command()
async def pannello(ctx):
    if ctx.channel.name != CANALE_LAVORO:
        await ctx.send("❌ Usa questo comando nel canale giusto!")
        return

    embed = discord.Embed(
        title="📋 TIMBRATURA LAVORO",
        description="Clicca i bottoni sotto",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=LavoroView())

# --- AVVIO ---
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("⚠️ Devi impostare il token!")

bot.run(TOKEN)
