"""
Test runner for Swing Trading Phase 1 with complete DB isolation
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from persistence import database as db
from tests import test_validation as tv
from tests import test_database as td
from tests import test_domain as td2


def run_all_tests():
    """Run all tests against an isolated test database."""
    print("=" * 60)
    print("Running Swing Trading Phase 1 Tests (Isolated Test DB)...")
    print("=" * 60)
    
    test_db_path = root_dir / "data" / "test_swing_trading.db"
    if test_db_path.exists():
        test_db_path.unlink()
        
    try:
        # 1. Switch to isolated test database
        db.set_db_path(test_db_path)
        db.init_db(test_db_path)
        db.seed_demo_data()
        
        # 2. Test validation rules
        print("\n--- 1. Validation Tests ---")
        tv.test_validate_setup_type()
        tv.test_validate_status()
        tv.test_validate_timeframe()
        tv.test_validate_price()
        tv.test_validate_level_type()
        tv.test_validate_priority()
        tv.test_get_all_setup_types()
        tv.test_get_all_statuses()
        tv.test_get_all_timeframes()
        
        # 3. Test database initialization and seeding
        print("\n--- 2. Database Tests ---")
        td.test_database_initialization()
        td.test_data_exists()
        td.test_get_stocks()
        
        # 4. Test domain logic, stock join, trade plan, levels, search, history
        print("\n--- 3. Domain & Feature Tests ---")
        td2.test_add_stock()
        td2.test_get_stock_by_ticker()
        td2.test_add_observation_with_trade_plan_and_levels()
        td2.test_stock_join_in_get_chart_observations()
        td2.test_search_filters()
        td2.test_stock_history_chronological()
        td2.test_update_observation_and_status_history()
        td2.test_dashboard_status_counts()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    finally:
        # Tear down test database and reset active path to production DB
        if test_db_path.exists():
            test_db_path.unlink()
        db.set_db_path(None)


if __name__ == "__main__":
    run_all_tests()

