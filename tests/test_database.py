# Database tests for Swing Trading Phase 1

from persistence import database as db


def test_database_initialization():
    db.init_db()
    import os
    assert os.path.exists(db.CURRENT_DB_PATH), "Database file should exist"
    print("✓ Database initialized")


def test_data_exists():
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        assert cursor.fetchone()[0] >= 2, "Should have demo stocks"
        print("✓ Demo data exists in database")
    finally:
        conn.close()


def test_get_stocks():
    from domain import services as ds
    stocks = ds.get_stocks()
    assert len(stocks) >= 2, "Should have at least 2 stocks"
    print("✓ Stocks retrieved")
