# Tests for validation

from domain import services as ds


def test_validate_setup_type():
    assert ds.validate_setup_type("Reversal") == True
    assert ds.validate_setup_type("Invalid") == False
    print("✓ Setup type validation works")


def test_validate_status():
    assert ds.validate_status("Watching") == True
    assert ds.validate_status("Invalid") == False
    print("✓ Status validation works")


def test_validate_timeframe():
    assert ds.validate_timeframe("Daily") == True
    assert ds.validate_timeframe("Invalid") == False
    print("✓ Timeframe validation works")


def test_validate_price():
    assert ds.validate_price(100.0) == True
    assert ds.validate_price(0) == False
    assert ds.validate_price(-10) == False
    print("✓ Price validation works")


def test_validate_level_type():
    assert ds.validate_level_type("Support") == True
    assert ds.validate_level_type("Invalid") == False
    print("✓ Level type validation works")


def test_validate_priority():
    assert ds.validate_priority("High") == True
    assert ds.validate_priority("Invalid") == False
    print("✓ Priority validation works")


def test_get_all_setup_types():
    setup_types = ds.get_all_setup_types()
    assert len(setup_types) == 7
    assert "Reversal" in setup_types
    print("✓ All setup types retrieved")


def test_get_all_statuses():
    statuses = ds.get_all_statuses()
    assert len(statuses) == 5
    assert "Watching" in statuses
    print("✓ All statuses retrieved")


def test_get_all_timeframes():
    timeframes = ds.get_all_timeframes()
    assert len(timeframes) == 4
    assert "Daily" in timeframes
    print("✓ All timeframes retrieved")
