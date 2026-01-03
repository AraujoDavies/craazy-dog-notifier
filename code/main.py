import discord
import asyncio
import os
from db import TblPerroLoko
from perro_loko import procurar_jogos_perro_loko, engine
from sqlalchemy import select, update

from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
TOKEN = os.getenv('DISCORD_TOKEN_PROD')

@client.event
async def on_ready():
    while True:
        procurar_jogos_perro_loko()
        stmt = select(TblPerroLoko.name, TblPerroLoko.placar, TblPerroLoko.odd_back_under, TblPerroLoko.market_id, TblPerroLoko.mercado, TblPerroLoko.tempo).where(TblPerroLoko.sinal_enviado == False)
        with engine.begin() as conn:
            sinais = conn.execute(stmt).fetchall()

        for sinal in sinais:
            placar = f' {sinal[1]} '
            linha = sinal[4].split('_')[-1][:1] + '.' + sinal[4].split('_')[-1][1:]
            url = 'https://www.betfair.bet.br/exchange/plus/football/market/' + sinal[3]
            msg = f":dog: :pill: Sinal Perro Loko :pill: :dog:\n\n{sinal[0].replace(' v ', placar)} '{int(sinal[5])}\nUnder {linha}: @{sinal[2]}\n[LINK BETFAIR]({url})\n------"
            channel = client.get_channel(CHANNEL_ID)
            await channel.send(msg)
            
            update_stmt = update(TblPerroLoko).where(TblPerroLoko.market_id==sinal[3]).values(sinal_enviado=True)
            with engine.begin() as conn:
                conn.execute(update_stmt)

        await asyncio.sleep(30)

client.run(TOKEN)