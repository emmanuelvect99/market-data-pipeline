import logging
from datetime import datetime, timezone
from src.pipeline import MarketPipeline
from src.repository import MarketRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Market Data Pipeline ===")

    # Initialize repository and setup DB (SQLite by default for instant testing)
    repo = MarketRepository()
    repo.setup_database()

    raw_market_ticks = [
        {"symbol": "aapl", "price": 185.50, "volume": 1200, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "msft", "price": 420.10, "volume": 850, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "aapl", "price": 186.00, "volume": 430, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "bad_ticker", "price": -50.0, "volume": 100},
        {"symbol": "goog", "price": 175.25, "volume": 3000, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "msft", "package": 421.50, "price": 421.50, "volume": 620, "timestamp": datetime.now(timezone.utc).isoformat()}
    ]

    try:
        pipeline = MarketPipeline(repository=repo)
        
        logger.info("--- Ingesting, validating, and persisting ticks ---")
        valid_ticks = pipeline.ingest(raw_market_ticks, persist=True)
        
        logger.info(f"Number of valid ticks retained: {len(valid_ticks)}")

        logger.info("--- Computing statistics per symbol ---")
        stats = pipeline.compute_statistics()
        
        logger.info(f"Total ticks processed: {stats['total_ticks']}")
        for symbol, data in stats["symbols"].items():
            logger.info(
                f"Symbol: {symbol} | "
                f"Tick Count: {data['tick_count']} | "
                f"Average Price: {data['average_price']} | "
                f"Total Volume: {data['total_volume']}"
            )

    except Exception as e:
        logger.error(f"An error occurred during pipeline execution: {e}")

    logger.info("=== Processing Complete ===")

if __name__ == "__main__":
    main()
