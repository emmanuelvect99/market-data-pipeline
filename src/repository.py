import os
import logging
import psycopg
from dotenv import load_dotenv
from src.schema import MarketTick

load_dotenv()
logger = logging.getLogger(__name__)

class MarketRepository:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.dbname = os.getenv("DB_NAME", "market_db")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")

    def _get_connection(self):
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )

    def insert_ticks(self, ticks: list[MarketTick]) -> int:
        if not ticks:
            return 0

        query = """
            INSERT INTO market_ticks (symbol, price, volume, timestamp)
            VALUES (%s, %s, %s, %s)
        """
        
        data = [
            (tick.symbol, tick.price, tick.volume, tick.timestamp)
            for tick in ticks
        ]

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(query, data)
                conn.commit()
            logger.info(f"{len(ticks)} ticks insérés avec succès dans PostgreSQL.")
            return len(ticks)
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion en base de données : {e}")
            raise