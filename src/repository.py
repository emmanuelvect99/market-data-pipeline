import os
import logging
import sqlite3
from dotenv import load_dotenv
from src.schema import MarketTick

load_dotenv()
logger = logging.getLogger(__name__)

class MarketRepository:
    def __init__(self):
        self.use_sqlite = os.getenv("USE_SQLITE", "True").lower() == "true"
        self.sqlite_path = os.getenv("SQLITE_PATH", "market_data.db")
        
        # PostgreSQL config
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.dbname = os.getenv("DB_NAME", "market_db")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")

    def _get_connection(self):
        if self.use_sqlite:
            return sqlite3.connect(self.sqlite_path)
        else:
            import psycopg
            return psycopg.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )

    def setup_database(self):
        """Creates the table if it doesn't exist (useful for SQLite demo)."""
        if self.use_sqlite:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS market_ticks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        price REAL NOT NULL,
                        volume INTEGER NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                conn.commit()
            logger.info("SQLite database initialized successfully.")

    def insert_ticks(self, ticks: list[MarketTick]) -> int:
        if not ticks:
            return 0

        if self.use_sqlite:
            query = """
                INSERT INTO market_ticks (symbol, price, volume, timestamp)
                VALUES (?, ?, ?, ?)
            """
            data = [
                (tick.symbol, tick.price, tick.volume, tick.timestamp.isoformat())
                for tick in ticks
            ]
            try:
                with self._get_connection() as conn:
                    conn.executemany(query, data)
                    conn.commit()
                logger.info(f"{len(ticks)} ticks successfully inserted into SQLite.")
                return len(ticks)
            except Exception as e:
                logger.error(f"Error inserting into SQLite: {e}")
                raise
        else:
            query = """
                INSERT INTO market_ticks (symbol, price, volume, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            data = [
                (tick.symbol, tick.price, tick.volume, tick.timestamp)
                for tick in ticks
            ]
            try:
                import psycopg
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.executemany(query, data)
                    conn.commit()
                logger.info(f"{len(ticks)} ticks successfully inserted into PostgreSQL.")
                return len(ticks)
            except Exception as e:
                logger.error(f"Error inserting into PostgreSQL: {e}")
                raise
