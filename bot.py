@bot.command()
async def ore(ctx, *, utente: discord.Member):
    log_channel = discord.utils.get(ctx.guild.text_channels, name="log-lavoro")

    if not log_channel:
        await ctx.send("❌ Canale log-lavoro non trovato.")
        return

    inizio = None
    totale_secondi = 0

    async for msg in log_channel.history(limit=1000):
        if utente.mention in msg.content:

            if "ha iniziato" in msg.content:
                try:
                    ora = msg.content.split("alle ")[1]
                    inizio = datetime.strptime(ora, "%H:%M:%S")
                except:
                    continue

            elif "ha finito" in msg.content and inizio:
                durata_text = msg.content.split("⏱ ")[1]
                ore = int(durata_text.split("h")[0])
                minuti = int(durata_text.split("h ")[1].replace("m", ""))

                totale_secondi += ore * 3600 + minuti * 60
                inizio = None

    ore_tot = totale_secondi // 3600
    minuti_tot = (totale_secondi % 3600) // 60

    await ctx.send(f"⏱ {utente.mention} ha lavorato: **{ore_tot}h {minuti_tot}m**")
