import logging
from datetime import datetime, timezone
from src.pipeline import MarketPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Démarrage du Market Data Pipeline ===")

    raw_market_ticks = [
        {"symbol": "aapl", "price": 185.50, "volume": 1200, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "msft", "price": 420.10, "volume": 850, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "aapl", "price": 186.00, "volume": 430, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "bad_ticker", "price": -50.0, "volume": 100},
        {"symbol": "goog", "price": 175.25, "volume": 3000, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "msft", "price": 421.50, "volume": 620, "timestamp": datetime.now(timezone.utc).isoformat()}
    ]

    try:
        pipeline = MarketPipeline()
        
        logger.info("--- Ingestion et validation des ticks ---")
        valid_ticks = pipeline.ingest(raw_market_ticks, persist=False)  # Mettre True si PostgreSQL est lancé
        
        logger.info(f"Nombre de ticks valides retenus : {len(valid_ticks)}")

        logger.info("--- Calcul des statistiques par symbole ---")
        stats = pipeline.compute_statistics()
        
        logger.info(f"Total des ticks traités : {stats['total_ticks']}")
        for symbol, data in stats["symbols"].items():
            logger.info(
                f"Symbole : {symbol} | "
                f"Nombre de ticks : {data['tick_count']} | "
                f"Prix moyen : {data['average_price']} | "
                f"Volume total : {data['total_volume']}"
            )

    except Exception as e:
        logger.error(f"Une erreur est survenue lors de l'exécution du pipeline : {e}")

    logger.info("=== Fin du traitement ===")

if __name__ == "__main__":
    main()