
# Carrega imports e funcoes auxiliares
from api_betfair import callAping, session_token, SESSION_TOKEN
import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
from helpers import *

from dotenv import load_dotenv

import logging
from db import engine


load_dotenv()
ignorar_events = [] # add o id dos eventos que sairam do padrão ou estao no banco

logging.basicConfig(
    level=logging.INFO,
    encoding='utf-8',
    format="%(asctime)s - %(levelname)s: %(message)s"
)

MINUTO_APROXIMADO = 80 # default 80
ODD_UNDER_AOS_88 = 1.24 # em busca da melhor odd ainda
LIQUIDEZ = 61000 # em busca da melhor liquidez ainda
GAP = 0.03


def procurar_jogos_perro_loko():
    """
        Identifica possiveis jogos que se encaixem no padrão.
    """
    logging.info('analisando jogos...')
    # listando jogos em andamento
    format_strdt = '%Y-%m-%dT%H:%M:%SZ'
    agr_utc = datetime.now(timezone.utc)
    maisxh_utc = agr_utc + timedelta(hours=2)
    dia_from = agr_utc.strftime(format_strdt)
    dia_to = maisxh_utc.strftime(format_strdt)

    rpc = """
    {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listEvents",
        "params": {
            "filter": {
                "eventTypeIds": [
                    "1"
                ],
                "inPlayOnly": "true"
            }
        },
    "id": 1}
    """.replace('dia_from', dia_from).replace('dia_to', dia_to)

    list_events = callAping(rpc)
    if type(list_events) == str:
        return logging.error(list_events)

    if 'result' not in list_events.keys():
        SESSION_TOKEN.append(session_token())
        logging.info('Renovando o session token!!')

    jogos_do_dia = []
    if 'result' in list_events.keys():
        for jogo in list_events['result']:
            jogos_do_dia.append(jogo['event'])

    df_events = pd.DataFrame(jogos_do_dia)

    if df_events.empty:
        return logging.info('Sem jogos...')

    df_events['minuto_aproximado'] = df_events['openDate'].map(lambda x: minutos_aproximados(x)) # Quantos minutos aprox o jogo tem

    df_events = df_events.sort_values('openDate')
    df_events.rename(columns={"id": "event_id"}, inplace=True)

    df_events = df_events[["event_id", "name", "minuto_aproximado"]]

    logging.info('Jogos ao vivo: %s', len(df_events))

    # # Filtrar jogos q estão no finalzinho +80 minutos (sem intervalo)
    df = df_events[df_events["minuto_aproximado"] > MINUTO_APROXIMADO].copy()
    logging.info('jogos com mais de %s minutos de horário de início: %s', MINUTO_APROXIMADO, len(df))

    if df.empty:
        return logging.info('SEM JOGOS...')

    event_ids = str(list(df['event_id']))
    for caracter in ["[", "]", " ", "'"]:
        event_ids = event_ids.replace(caracter, '')

    df.set_index('event_id', inplace=True) # event_id vira index...

    score_details = event_timelines(event_ids)

    ## coletando estatísticas...
    for stats in score_details:
        event_id = str(stats['eventId'])
        home_score = stats["score"]["home"]["score"]
        away_score = stats["score"]["away"]["score"]
        mercado = "OVER_UNDER_"
        mercado += str(float(home_score) + float(away_score) + 0.5).replace('.', '')

        df.loc[event_id, "placar"] = f"{home_score} - {away_score}"
        df.loc[event_id, "tempo"] = stats["timeElapsed"]
        df.loc[event_id, "inPlayMatchStatus"] = stats["inPlayMatchStatus"]
        df.loc[event_id, "status"] = stats["status"] # IN_PLAY
        
        df.loc[event_id, "mercado"] = mercado

    if 'mercado' not in df.columns:
        return logging.warning('Não coletou estatísticas!')

    df = df[~df['mercado'].isna()] # remove mercados nulos
    for market in df['mercado'].unique():
        event_ids = str(list(df[df['mercado'] == market].index)).replace("'", '"')

        rpc = """
        {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketCatalogue",
        "params": {
            "filter": {
                "eventIds": <event_ids>,
                "marketTypeCodes": ["<mercado>"]
            },
            "marketProjection": [
            "EVENT"
            ],
            "maxResults": "200"
        },
        "id": 1
        }
        """.replace(
            '<event_ids>', event_ids # ["id1", "id2", "idn"]
        ).replace(
            '<mercado>', market
        ) 

        market_catalogue = callAping(rpc)

        market_catalogue

        if type(market_catalogue) == str:
            return logging.error(market_catalogue)

        if 'result' in market_catalogue.keys():
            for market in market_catalogue['result']:
                if 'Over/Under' not in market['marketName']:
                    logging.error('mercado inválido: %s', market)
                    continue

                event_id = market['event']['id']
                df.loc[event_id, "market_id"] = market["marketId"]


    # coletando GAP, ODDS, valor correspondido, etc do MO
    if 'market_id' not in df.columns:
        df_str = df_log.to_string(index=False)
        return logging.warning('DF não possui a coluna: "market_id": %s', df_str)

    market_ids = str(list(df[~df['market_id'].isna()]['market_id'])).replace("'", '"')
    rpc = """{
        "jsonrpc": "2.0", 
        "method": "SportsAPING/v1.0/listMarketBook", 
        "params": { 
            "marketIds": <market_id>,
            "marketProjection": [
                "EVENT",
                "MARKET_DESCRIPTION",
                "RUNNER_METADATA"
            ],
            "priceProjection": {      
                "priceData": ["EX_BEST_OFFERS"]
            }
        },
        "id": 1
    }""".replace('<market_id>', market_ids)

    market_books = callAping(rpc)

    if type(market_books) == str:
        return logging.error(market_books)


    if 'result' in market_books.keys():
        for mb in market_books['result']:
            event_id = df[df['market_id'] == mb['marketId']].index[0]
            mbr = mb['runners']

            df.loc[event_id, "status"] = mb['status']
            df.loc[event_id, "betDelay"] = mb['betDelay']
            df.loc[event_id, "totalMatched"] = mb['totalMatched']

            df.loc[event_id, "selection_id"] = str(mbr[0]['selectionId'])
            try:
                df.loc[event_id, "gap"] = mbr[0]['ex']['availableToLay'][0]['price'] - mbr[0]['ex']['availableToBack'][0]['price']
                df.loc[event_id, "odd_back_under"] = mbr[0]['ex']['availableToBack'][0]['price']
                # df.loc[event_id, "odd_back_visitante"] = mbr[1]['ex']['availableToBack'][0]['price']
            except:
                df.loc[event_id, "gap"] = 1000
                df.loc[event_id, "odd_back_under"] = 1.01
                # df.loc[event_id, "odd_back_visitante"] = 1000

            df.loc[event_id, "runners"] = str(mbr)
            df.loc[event_id, "dt_insert"] = datetime.now()

    if 'minuto_aproximado' in df.columns:
        df.pop('minuto_aproximado')

    colunas_log = ['name', 'placar', 'tempo', 'status', 'mercado', 'market_id', 'betDelay', 'totalMatched', 'gap', 'odd_back_under']
    for col in colunas_log:
        if col not in df.columns:
            return logging.error('Não encontrou a coluna: %s', col)

    df_log = df[colunas_log]
    df_log = df_log[df_log["tempo"] >= 84]
    if df_log.empty == False:
        logging.info(df_log.to_string(index=False))

    df['sinal_enviado'] = False
    open = (df['status'] == 'OPEN')
    five_sec = (df['betDelay'] == 5) # 5 seg
    gap = (df['gap'] < GAP) # 0.04
    tempo = (df['tempo'] >= 87) & (df['tempo'] <= 88)
    odd_back_under = (df['odd_back_under'] > ODD_UNDER_AOS_88) 
    liquidez  = (df['totalMatched'] > LIQUIDEZ)

    padrao_craazy_dog = open & five_sec & gap & tempo & odd_back_under & liquidez

    df = df[padrao_craazy_dog].copy()
    logging.info("jogos no padrão PERRO LOKO: %s", len(df))

    # adicionar no DB
    for index in df.index:
        event_id = index
        if event_id in ignorar_events: continue
        logging.info('Salvando jogo event id: %s', event_id)
        
        try:
            df_db = df[df.index == index].copy()
            df_db.to_sql(name="perro_loko", con=engine, if_exists="append", index=True)
            if event_id not in ignorar_events: ignorar_events.append(event_id)
        except Exception as error:
            logging.error("DB event_id %s: %s", event_id, str(error))
            pass


if __name__ == '__main__':
    procurar_jogos_perro_loko()