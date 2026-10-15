import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.schema import MarketTick, validate_and_filter_ticks

def test_valid_tick_normalization():
    data = {"symbol": "  aapl  ", "price": 150.5, "volume": 1000}
    tick = MarketTick(**data)
    assert tick.symbol == "AAPL"
    assert tick.price == 150.5
    assert tick.volume == 1000
    assert tick.timestamp.tzinfo == timezone.utc

def test_invalid_price_raises_validation_error():
    data = {"symbol": "aapl", "price": -10.0, "volume": 1000}
    with pytest.raises(ValidationError) as exc_info:
        MarketTick(**data)
    assert "price" in str(exc_info.value)

def test_validate_and_filter_ticks():
    raw_data = [
        {"symbol": "aapl", "price": 150.0, "volume": 500},
        {"symbol": "msft", "price": -50.0, "volume": 200},
        {"symbol": "", "price": 100.0, "volume": 100},
        {"symbol": "goog", "price": 2800.0, "volume": 50}
    ]
    
    valid_ticks = validate_and_filter_ticks(raw_data)
    assert len(valid_ticks) == 2
    assert valid_ticks[0].symbol == "AAPL"
    assert valid_ticks[1].symbol == "GOOG"