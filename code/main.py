import asyncio
import logging
import os
import sys

import discord
from db import TblPerroLoko, engine
from dotenv import load_dotenv

# from perro_loko import procurar_jogos_perro_loko
from sqlalchemy import select, update

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_ID_LOG = int(os.getenv("CHANNEL_ID_LOG"))
TOKEN = os.getenv("DISCORD_TOKEN_PROD")


@client.event
async def on_ready():
    log_channel = client.get_channel(CHANNEL_ID_LOG)
    await log_channel.send("PERRO LOKO ON!")

    while True:
        # try:
        #     procurar_jogos_perro_loko()
        # except Exception as error:
        #     logging.error('msg -> %s', str(error))
        #     await log_channel.send('PERRO LOKO ERROR!')
        #     await asyncio.sleep(30)

        try:
            stmt = select(
                TblPerroLoko.name,
                TblPerroLoko.placar,
                TblPerroLoko.odd_back_under,
                TblPerroLoko.market_id,
                TblPerroLoko.mercado,
                TblPerroLoko.tempo,
            ).where(TblPerroLoko.sinal_enviado == False)
            with engine.begin() as conn:
                sinais = conn.execute(stmt).fetchall()

            for sinal in sinais:
                placar = f" {sinal[1]} "
                linha = sinal[4].split("_")[-1][:1] + "." + sinal[4].split("_")[-1][1:]
                url = (
                    "https://www.betfair.bet.br/exchange/plus/football/market/"
                    + sinal[3]
                )
                msg = f":dog: :pill: Sinal Perro Loko :pill: :dog:\n\n{sinal[0].replace(' v ', placar)} '{int(sinal[5])}\nUnder {linha}: @{sinal[2]}\n[LINK BETFAIR]({url})\n------"
                channel = client.get_channel(CHANNEL_ID)
                await channel.send(msg)

                update_stmt = (
                    update(TblPerroLoko)
                    .where(TblPerroLoko.market_id == sinal[3])
                    .values(sinal_enviado=True)
                )
                with engine.begin() as conn:
                    conn.execute(update_stmt)

            await asyncio.sleep(30)
        except Exception as error:
            logging.error("FAIL >>>> %s", str(error))
            await asyncio.sleep(10)
            sys.exit()


client.run(TOKEN)
