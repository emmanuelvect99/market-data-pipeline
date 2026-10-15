CREATE TABLE IF NOT EXISTS market_ticks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price NUMERIC(12, 4) NOT NULL CHECK (price > 0),
    volume INTEGER NOT NULL CHECK (volume >= 0),
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_ticks_symbol_timestamp 
ON market_ticks (symbol, timestamp);