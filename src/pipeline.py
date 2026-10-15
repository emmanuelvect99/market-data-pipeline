import logging
from collections import defaultdict
from src.schema import validate_and_filter_ticks, MarketTick
from src.repository import MarketRepository

logger = logging.getLogger(__name__)

class MarketPipeline:
    def __init__(self, repository: MarketRepository = None):
        self.stored_ticks: list[MarketTick] = []
        self.repository = repository or MarketRepository()

    def ingest(self, raw_data: list[dict], persist: bool = True) -> list[MarketTick]:
        valid_ticks = validate_and_filter_ticks(raw_data)
        
        if valid_ticks:
            self.stored_ticks.extend(valid_ticks)
            logger.info(f"{len(valid_ticks)} ticks valides ingérés.")
            
            if persist:
                try:
                    self.repository.insert_ticks(valid_ticks)
                except Exception as e:
                    logger.error(f"La persistance en base a échoué, mais les ticks restent en mémoire : {e}")
                    
        return valid_ticks

    def compute_statistics(self) -> dict:
        if not self.stored_ticks:
            return {
                "total_ticks": 0,
                "symbols": {}
            }

        stats_by_symbol = defaultdict(lambda: {"count": 0, "price_sum": 0.0, "total_volume": 0})

        for tick in self.stored_ticks:
            s = stats_by_symbol[tick.symbol]
            s["count"] += 1
            s["price_sum"] += tick.price
            s["total_volume"] += tick.volume

        result_symbols = {}
        for symbol, data in stats_by_symbol.items():
            count = data["count"]
            result_symbols[symbol] = {
                "tick_count": count,
                "average_price": round(data["price_sum"] / count, 4) if count > 0 else 0.0,
                "total_volume": data["total_volume"]
            }

        return {
            "total_ticks": len(self.stored_ticks),
            "symbols": result_symbols
        }