-- Database: swing_trading.db
-- Phase 1: Chart Observation Record-Keeping MVP

-- Stocks table
CREATE TABLE IF NOT EXISTS stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    sector TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chart observations table
CREATE TABLE IF NOT EXISTS chart_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER NOT NULL,
    observation_date DATE NOT NULL,
    timeframe TEXT NOT NULL CHECK(timeframe IN ('Weekly', 'Daily', '4H', '1H')),
    market_structure TEXT,
    setup_type TEXT NOT NULL CHECK(setup_type IN ('Breakout', 'Breakdown', 'Reversal', 'Pullback', 'Continuation', 'Range', 'No Setup')),
    pattern TEXT,
    status TEXT NOT NULL CHECK(status IN ('Watching', 'Triggered', 'Confirmed', 'Failed', 'Expired')),
    summary TEXT,
    key_observation TEXT,
    notes TEXT,
    entry_price_from REAL,
    entry_price_to REAL,
    stop_loss_from REAL,
    stop_loss_to REAL,
    target_price_from REAL,
    target_price_to REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks(id)
);

-- Price levels table
CREATE TABLE IF NOT EXISTS price_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    level_type TEXT NOT NULL CHECK(level_type IN ('Support', 'Resistance', 'Breakout Trigger', 'Breakdown Trigger', 'Invalidation', 'Target')),
    label TEXT,
    price_from REAL NOT NULL,
    price_to REAL,
    priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES chart_observations(id)
);

-- Observation history table (tracks status changes)
CREATE TABLE IF NOT EXISTS observation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (observation_id) REFERENCES chart_observations(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker);
CREATE INDEX IF NOT EXISTS idx_observations_stock_id ON chart_observations(stock_id);
CREATE INDEX IF NOT EXISTS idx_observations_status ON chart_observations(status);
CREATE INDEX IF NOT EXISTS idx_observations_setup_type ON chart_observations(setup_type);
CREATE INDEX IF NOT EXISTS idx_observations_pattern ON chart_observations(pattern);
CREATE INDEX IF NOT EXISTS idx_price_levels_observation_id ON price_levels(observation_id);
CREATE INDEX IF NOT EXISTS idx_observation_history_observation_id ON observation_history(observation_id);
