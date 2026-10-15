import pytest
from datetime import datetime, timezone
from src.pipeline import MarketPipeline

def test_pipeline_statistics():
    pipeline = MarketPipeline()
    
    raw_data = [
        {"symbol": "aapl", "price": 100.0, "volume": 10, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "aapl", "price": 200.0, "volume": 20, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"symbol": "msft", "price": 50.0, "volume": 5}
    ]
    
    valid_ticks = pipeline.ingest(raw_data, persist=False)
    assert len(valid_ticks) == 3
    
    stats = pipeline.compute_statistics()
    assert stats["total_ticks"] == 3
    
    # Check AAPL stats
    aapl_stats = stats["symbols"]["AAPL"]
    assert aapl_stats["tick_count"] == 2
    assert aapl_stats["average_price"] == 150.0
    assert aapl_stats["total_volume"] == 30
    
    # Check MSFT stats
    msft_stats = stats["symbols"]["MSFT"]
    assert msft_stats["tick_count"] == 1
    assert msft_stats["average_price"] == 50.0
    assert msft_stats["total_volume"] == 5
