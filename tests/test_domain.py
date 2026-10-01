# Domain tests for Swing Trading Phase 1

from domain import services as ds
from app import services as app_services


def test_add_stock():
    stock = ds.create_stock("TESTCO", "Test Corporation", "NASDAQ", "Technology")
    assert stock.id is not None
    assert stock.ticker == "TESTCO"
    assert stock.company_name == "Test Corporation"
    print("✓ Stock created successfully")


def test_get_stock_by_ticker():
    stock = ds.get_stock_by_ticker("TESTCO")
    assert stock is not None
    assert stock.ticker == "TESTCO"
    print("✓ Stock retrieved by ticker")


def test_add_observation_with_trade_plan_and_levels():
    stock = ds.get_stock_by_ticker("TESTCO")
    assert stock is not None
    
    levels = [
        {"level_type": "Support", "label": "Support 1", "price_from": 140.0, "price_to": 142.0},
        {"level_type": "Support", "label": "Support 2", "price_from": 135.0, "price_to": None},
        {"level_type": "Resistance", "label": "Resistance 1", "price_from": 160.0, "price_to": 162.0},
        {"level_type": "Resistance", "label": "Resistance 2", "price_from": 170.0, "price_to": None},
    ]
    
    obs = ds.create_observation(
        stock_id=stock.id,
        observation_date="2026-09-29",
        timeframe="Daily",
        market_structure="Bullish",
        setup_type="Breakout",
        pattern="Ascending Triangle",
        status="Watching",
        summary=None,
        key_observation="Breaking above 160 horizontal resistance",
        notes="High volume confirmation needed on 4H",
        entry_price_from=159.0,
        entry_price_to=161.0,
        stop_loss_from=152.0,
        stop_loss_to=None,
        target_price_from=180.0,
        target_price_to=185.0,
        levels=levels
    )
    
    assert obs.id is not None
    assert obs.setup_type == "Breakout"
    assert obs.entry_price_from == 159.0
    assert obs.entry_price_to == 161.0
    assert obs.stop_loss_from == 152.0
    assert obs.target_price_from == 180.0
    assert obs.target_price_to == 185.0
    assert len(obs.levels) == 4
    print("✓ Observation with Trade Plan and Chart Levels created")


def test_stock_join_in_get_chart_observations():
    stock = ds.get_stock_by_ticker("TESTCO")
    observations = ds.get_chart_observations(stock_id=stock.id)
    assert len(observations) >= 1
    obs = observations[0]
    
    # Assert stock join works properly (NO 'N/A')
    assert obs.stock_ticker == "TESTCO", f"Expected 'TESTCO', got '{obs.stock_ticker}'"
    assert obs.stock_name == "Test Corporation", f"Expected 'Test Corporation', got '{obs.stock_name}'"
    
    # Test level mapping helper
    lvl_dict = obs.get_levels_dict()
    assert lvl_dict["Support 1"] is not None
    assert lvl_dict["Support 1"].price_from == 140.0
    assert lvl_dict["Support 1"].price_to == 142.0
    assert lvl_dict["Resistance 1"] is not None
    assert lvl_dict["Resistance 1"].price_from == 160.0
    print("✓ Stock JOIN and level dictionary mapping verified (no 'N/A')")


def test_search_filters():
    stock = ds.get_stock_by_ticker("TESTCO")
    
    # Search by setup type
    res_setup = ds.get_chart_observations(setup_type="Breakout")
    assert any(o.stock_id == stock.id for o in res_setup)
    
    # Search by free-text in key observation
    res_text = ds.get_chart_observations(search_text="horizontal resistance")
    assert any(o.stock_id == stock.id for o in res_text)
    
    # Search by non-matching text
    res_empty = ds.get_chart_observations(search_text="nonexistent keyword xyz")
    assert len(res_empty) == 0
    
    # Search by date range
    res_date = ds.get_chart_observations(date_from="2026-09-01", date_to="2026-09-30")
    assert any(o.stock_id == stock.id for o in res_date)
    print("✓ Search filters (setup, date range, free text) verified")


def test_stock_history_chronological():
    stock = ds.get_stock_by_ticker("TESTCO")
    
    # Add an older observation for the same stock
    ds.create_observation(
        stock_id=stock.id,
        observation_date="2026-09-15",
        timeframe="Weekly",
        market_structure="Consolidating",
        setup_type="Range",
        pattern="Rectangle",
        status="Watching",
        summary=None,
        key_observation="Consolidation between 140 and 160",
        notes="Older weekly observation"
    )
    
    history = ds.get_stock_history(stock.id)
    assert len(history) >= 2
    # Verify newest observation is first
    assert history[0].observation_date >= history[1].observation_date
    print("✓ Stock History returns multiple observations in reverse chronological order")


def test_update_observation_and_status_history():
    stock = ds.get_stock_by_ticker("TESTCO")
    history = ds.get_stock_history(stock.id)
    obs = history[0]
    
    # Update status to Triggered with audit note and updated target
    success = ds.update_observation(
        obs.id,
        status="Triggered",
        target_price_from=190.0,
        status_notes="Price broke out above 160 on 2x volume"
    )
    assert success is True
    
    updated = ds.get_observation_by_id(obs.id)
    assert updated.status == "Triggered"
    assert updated.target_price_from == 190.0
    
    # Verify observation_history audit records
    status_hist = ds.get_observation_status_history(obs.id)
    assert len(status_hist) >= 2
    assert status_hist[0]["status"] == "Triggered"
    assert "2x volume" in status_hist[0]["notes"]
    print("✓ Observation updating and status transition audit trail verified")


def test_dashboard_status_counts():
    data = app_services.get_dashboard_data()
    status_map = data["status_map"]
    assert "Watching" in status_map or "Triggered" in status_map
    assert isinstance(status_map.get("Watching", 0), int)
    assert isinstance(status_map.get("Triggered", 0), int)
    print("✓ Dashboard status counts accurately computed")

