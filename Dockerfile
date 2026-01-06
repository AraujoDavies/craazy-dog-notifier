FROM python:3.11.10

COPY requirements.txt /app/requirements.txt
COPY betfair-init/ /app/betfair-init/

WORKDIR /app

RUN pip install -r requirements.txt

# app key valid to all accounts
ENV APP_KEY=gBMF1zhAoNgJIbxw
# set your db conn or use default
ENV DATABASE_URI=sqlite:///perro_loko.db

ENV TZ=America/Sao_Paulo
# betfair files path
ENV CRT_DIR=/app/betfair-init/client-2048.crt
ENV KEY_DIR=/app/betfair-init/client-2048.key