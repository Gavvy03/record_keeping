# Swing Trading System - Phase 1

A simple Chart Observation Record-Keeping MVP for swing trading analysis.

## Features

- Record stock chart observations
- Track price levels (Support/Resistance/Targets)
- Monitor observation status and history
- Filter and search observations

## Tech Stack

- **Python** - Backend logic
- **Streamlit** - Local web application
- **SQLite** - Local database
- **Pandas** - Data manipulation

## Project Structure

```
swing/
├── app/
│   ├── main.py          # Streamlit app entry point
│   └── services.py      # Application services
├── domain/
│   └── services.py      # Business logic (no database)
├── persistence/
│   └── database.py      # Database operations
├── db/
│   └── schema.sql       # Database schema
├── data/                # SQLite database (generated)
├── tests/               # Tests
│   ├── run_tests.py     # Test runner
│   ├── test_*.py        # Test modules
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## Installation

```bash
# Clone the repository (or use this directory)
cd swing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Database Setup

The database is initialized automatically on first run. Demo data for HBLENG and ONEGLOBAL is included.

## Running the App

```bash
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`.

## Usage

### 1. Dashboard
- View observation counts by status (Watching, Triggered, etc.)
- Status breakdown bar chart
- Recent observations table

### 2. Add Observation
- Register new stocks (Ticker, Company Name, Exchange, Sector)
- Record observations with Timeframe, Setup Type, Pattern, Market Structure, and Status
- Trade Plan (Entry, Stop Loss, Target — single price or range)
- Chart Levels (Fixed slots: Support 1..3 and Resistance 1..3 — single price or range)
- Technical Analysis (Key Observation, Notes)

### 3. Search / History
- Multi-criteria filtering by Stock, Setup Type, Status, Pattern, Market Structure, and Date Range
- Free-text search across Key Observation and Notes
- Compact, clickable results table with quick navigation to Observation Detail

### 4. Watchlist
- Browse active observations with stock ticker and company details
- Filter by status and setup type
- Full export to CSV with Trade Plan and Chart Levels

### 5. Stock History / Observation Detail
- View complete chronological history for any selected stock (newest first)
- Inspect Trade Plan, Support/Resistance levels, and Analysis
- Status Transition audit trail showing timestamped changes and notes
- Full observation editor to modify observation fields, Trade Plan, and Chart Levels

## Database Schema

### stocks
- `id` - Primary key
- `ticker` - Unique stock ticker
- `company_name` - Full company name
- `exchange` - Exchange code
- `sector` - Industry sector

### chart_observations
- `id` - Primary key
- `stock_id` - Foreign key to stocks
- `observation_date` - Date of observation
- `timeframe` - Weekly/Daily/4H/1H
- `market_structure` - Market trend description
- `setup_type` - Breakout/Breakdown/Reversal/Pullback/Continuation/Range/No Setup
- `pattern` - Chart pattern name
- `status` - Watching/Triggered/Confirmed/Failed/Expired
- `summary` - Brief summary
- `key_observation` - Key insight
- `notes` - Additional notes
- `entry_price_from`, `entry_price_to` - Trade Plan entry (single or range)
- `stop_loss_from`, `stop_loss_to` - Trade Plan stop loss (single or range)
- `target_price_from`, `target_price_to` - Trade Plan target (single or range)

### price_levels
- `id` - Primary key
- `observation_id` - Foreign key to chart_observations
- `level_type` - Support/Resistance
- `label` - Support 1..3 / Resistance 1..3
- `price_from` - Lower bound / single price
- `price_to` - Upper bound (optional for range)
- `priority` - High/Medium/Low
- `notes` - Additional notes

### observation_history
- `id` - Primary key
- `observation_id` - Foreign key to chart_observations
- `status` - Status at this point
- `changed_at` - Timestamp
- `notes` - Change notes

## Validation

- Ticker: 1-10 characters
- Price: must be positive
- Setup type: from predefined list
- Status: from predefined list
- Timeframe: Weekly/Daily/4H/1H
- Level type: from predefined list
- Priority: High/Medium/Low

## Demo Data

The app includes demo data for:
- **HBLENG** (HBL Engine Limited): Reversal setup, double bottom pattern
- **ONEGLOBAL** (One Global): Breakdown setup, channel pattern

## Running Tests

```bash
cd tests
python3 run_tests.py
```

## What's NOT Implemented (Phase 1)

- Live market data integration
- Automatic pattern detection
- Technical indicators
- Alerts
- Trading execution
- Broker integration
- Multi-user support

## Future Phases

- **Phase 2**: Automatic monitoring and alerts
- **Phase 3**: Pattern recognition and indicators
- **Phase 4**: Execution integration
