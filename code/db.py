from sqlalchemy import create_engine
import os

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base

from dotenv import load_dotenv
load_dotenv()

engine = create_engine(os.getenv('DATABASE_URI')) # "mysql+pymysql://root:admin@localhost:3306/betfairApps"
session = Session(engine)
Base = declarative_base()


class TblPerroLoko(Base):
    __tablename__ = "perro_loko"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, unique=True)
    name = Column(String(255), nullable=False)
    placar = Column(String(10), nullable=False)
    tempo = Column(Float, nullable=False)
    inPlayMatchStatus = Column(String(100))
    mercado = Column(String(100))
    status = Column(String(100)) # OPEN ou FINISH
    market_id = Column(String(50), nullable=False)
    selection_id = Column(String(50), nullable=False)
    betDelay = Column(Float, nullable=False)
    gap = Column(Float, nullable=False)
    totalMatched = Column(Float, nullable=False)
    odd_back_under = Column(Float, nullable=False)
    dt_insert = Column(DateTime)
    runners = Column(Text, nullable=False)
    sinal_enviado = Column(Boolean, default=False)


    def __repr__(self):
        return f"<match event_id={self.event_id} name={self.name}>"


if __name__ == '__main__':
    Base.metadata.create_all(engine)
