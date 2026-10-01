import sqlite3
from datetime import datetime
from pathlib import Path


DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "swing_trading.db"
CURRENT_DB_PATH = DB_PATH


def set_db_path(path=None):
    """Set active database path (useful for test isolation)."""
    global CURRENT_DB_PATH
    CURRENT_DB_PATH = Path(path) if path else DB_PATH


def ensure_db_dir(db_path=None):
    """Create data directory if it doesn't exist."""
    path = Path(db_path) if db_path else CURRENT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)


def get_connection(db_path=None):
    """Get database connection."""
    target_path = Path(db_path) if db_path else CURRENT_DB_PATH
    ensure_db_dir(target_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_columns(conn):
    """Ensure newly introduced columns exist in chart_observations table."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(chart_observations)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    
    new_cols = [
        ("entry_price_from", "REAL"),
        ("entry_price_to", "REAL"),
        ("stop_loss_from", "REAL"),
        ("stop_loss_to", "REAL"),
        ("target_price_from", "REAL"),
        ("target_price_to", "REAL"),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE chart_observations ADD COLUMN {col_name} {col_type}")
    conn.commit()


def cleanup_test_data(conn):
    """Clean up contaminated test records from previous test runs if any."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM stocks WHERE ticker = 'TEST'")
    test_stocks = cursor.fetchall()
    for row in test_stocks:
        stock_id = row["id"]
        cursor.execute("SELECT id FROM chart_observations WHERE stock_id = ?", (stock_id,))
        obs_ids = [r["id"] for r in cursor.fetchall()]
        for obs_id in obs_ids:
            cursor.execute("DELETE FROM price_levels WHERE observation_id = ?", (obs_id,))
            cursor.execute("DELETE FROM observation_history WHERE observation_id = ?", (obs_id,))
        cursor.execute("DELETE FROM chart_observations WHERE stock_id = ?", (stock_id,))
        cursor.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()


def init_db(db_path=None):
    """Initialize database with schema and ensure columns exist."""
    target_path = Path(db_path) if db_path else CURRENT_DB_PATH
    ensure_db_dir(target_path)
    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    conn = get_connection(target_path)
    try:
        with open(schema_path, "r") as f:
            schema = f.read()
        conn.executescript(schema)
        ensure_columns(conn)
        cleanup_test_data(conn)
        conn.commit()
    finally:
        conn.close()


def seed_demo_data():
    """Add demo data for HBLENG and ONEGLOBAL."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Insert stocks
        stocks = [
            ("HBLENG", "HBL Engine Limited", "PSX", "Automotive"),
            ("ONEGLOBAL", "One Global", "PSX", "Textile"),
        ]
        
        for ticker, name, exchange, sector in stocks:
            cursor.execute("""
                INSERT OR IGNORE INTO stocks (ticker, company_name, exchange, sector)
                VALUES (?, ?, ?, ?)
            """, (ticker, name, exchange, sector))
        
        conn.commit()
        
        # Get stock IDs
        cursor.execute("SELECT id, ticker FROM stocks")
        stock_map = {row["ticker"]: row["id"] for row in cursor.fetchall()}
        
        hbl_id = stock_map["HBLENG"]
        one_id = stock_map["ONEGLOBAL"]
        
        # Insert HBLENG observation
        hbl_obs_id = insert_chart_observation(
            conn, hbl_id, "2026-09-28", "Daily", "Bullish", "Reversal", 
            "Potential Double Bottom", "Watching",
            "Price forming double bottom near support", 
            "Key level at 820 breakout",
            "Need volume confirmation"
        )
        
        # Insert HBLENG price levels
        insert_price_level(
            conn, hbl_obs_id, "Support", "Support Zone", 720.0, 740.0, "High",
            "Primary support zone"
        )
        insert_price_level(
            conn, hbl_obs_id, "Support", "Structural Support", 650.0, 670.0, "Medium",
            "Strong historical support"
        )
        insert_price_level(
            conn, hbl_obs_id, "Breakout Trigger", "Breakout Level", 820.0, None, "High",
            "Key resistance to break"
        )
        insert_price_level(
            conn, hbl_obs_id, "Invalidation", "Double Bottom Invalidation", 650.0, None, "High",
            "Break below invalidates pattern"
        )
        insert_price_level(
            conn, hbl_obs_id, "Target", "Target Zone", 900.0, 950.0, "Medium",
            "Expected upside if breakout confirms"
        )
        
        # Insert ONEGLOBAL observation
        one_obs_id = insert_chart_observation(
            conn, one_id, "2026-09-27", "Weekly", "Bearish", "Breakdown",
            "Downward Channel", "Watching",
            "Price breaking below channel support", 
            "Weekly close below 450 is key",
            "Monitor volume on breakdown"
        )
        
        # Insert ONEGLOBAL price levels
        insert_price_level(
            conn, one_obs_id, "Resistance", "Channel Resistance", 520.0, 540.0, "High",
            "Upper boundary of channel"
        )
        insert_price_level(
            conn, one_obs_id, "Breakdown Trigger", "Breakdown Level", 450.0, None, "High",
            "Channel support break"
        )
        insert_price_level(
            conn, one_obs_id, "Target", "Target Zone", 400.0, 420.0, "Medium",
            "Expected downside if breakdown confirms"
        )
        
        conn.commit()
    finally:
        conn.close()


def insert_chart_observation(conn, stock_id, observation_date, timeframe, market_structure,
                             setup_type, pattern, status, summary, key_observation, notes,
                             entry_price_from=None, entry_price_to=None,
                             stop_loss_from=None, stop_loss_to=None,
                             target_price_from=None, target_price_to=None):
    """Insert a chart observation and return its ID."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chart_observations 
        (stock_id, observation_date, timeframe, market_structure, setup_type, 
         pattern, status, summary, key_observation, notes,
         entry_price_from, entry_price_to, stop_loss_from, stop_loss_to,
         target_price_from, target_price_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (stock_id, observation_date, timeframe, market_structure, setup_type,
          pattern, status, summary, key_observation, notes,
          entry_price_from, entry_price_to, stop_loss_from, stop_loss_to,
          target_price_from, target_price_to))
    obs_id = cursor.lastrowid
    
    # Insert initial status in history
    cursor.execute("""
        INSERT INTO observation_history (observation_id, status, notes)
        VALUES (?, ?, ?)
    """, (obs_id, status, "Observation created"))
    
    return obs_id


def insert_price_level(conn, observation_id, level_type, label, price_from, 
                       price_to=None, priority=None, notes=None):
    """Insert a price level."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO price_levels 
        (observation_id, level_type, label, price_from, price_to, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (observation_id, level_type, label, price_from, price_to, priority, notes))
    return cursor.lastrowid


def get_price_levels_by_observation_ids(conn, observation_ids):
    """Fetch all price levels for multiple observation IDs in one query."""
    if not observation_ids:
        return {}
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in observation_ids)
    cursor.execute(f"""
        SELECT * FROM price_levels 
        WHERE observation_id IN ({placeholders})
        ORDER BY level_type, label, price_from
    """, list(observation_ids))
    levels_by_obs = {obs_id: [] for obs_id in observation_ids}
    for row in cursor.fetchall():
        levels_by_obs[row["observation_id"]].append(row)
    return levels_by_obs


def update_observation_status(conn, observation_id, new_status, notes=None):
    """Update observation status and record in history."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE chart_observations 
        SET status = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), observation_id))
    
    cursor.execute("""
        INSERT INTO observation_history (observation_id, status, notes)
        VALUES (?, ?, ?)
    """, (observation_id, new_status, notes))
    
    return cursor.rowcount > 0


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database initialized and demo data seeded.")
