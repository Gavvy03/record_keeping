"""
Application services for Swing Trading Phase 1 Chart Observation Journal
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from domain.services import (
    get_stocks, get_chart_observations, create_stock, create_observation,
    get_observations_by_stock, get_recent_observations, get_observations_counts_by_status,
    get_all_setup_types, get_all_statuses, get_all_timeframes,
    get_all_level_types, get_all_priorities, get_observation_by_id,
    update_observation, create_price_level, update_price_level, delete_price_level,
    get_observation_status_history, get_stock_by_ticker, get_stock_history,
    validate_ticker
)


def get_dashboard_data():
    """Get aggregated data for dashboard view."""
    counts = get_observations_counts_by_status()
    status_map = {row["status"]: row["count"] for row in counts}
    return {
        "counts_by_status": counts,
        "status_map": status_map,
        "recent_observations": get_recent_observations(10),
        "total_stocks": len(get_stocks()),
        "total_observations": len(get_chart_observations())
    }


def get_watchlist_data(stock_filter=None, setup_filter=None, 
                       pattern_filter=None, status_filter=None,
                       market_structure_filter=None, date_from=None,
                       date_to=None, search_text=None):
    """Get filtered observations using SQL queries."""
    return get_chart_observations(
        stock_id=stock_filter,
        status=status_filter,
        setup_type=setup_filter,
        pattern=pattern_filter,
        market_structure=market_structure_filter,
        date_from=date_from,
        date_to=date_to,
        search_text=search_text
    )


def create_new_stock_form(ticker: str, company_name: str, 
                          exchange: str, sector: str):
    """Handle stock creation from form."""
    ticker_clean = (ticker or "").strip().upper()
    if not ticker_clean:
        return None, "Ticker symbol is required"
    if not validate_ticker(ticker_clean):
        return None, "Ticker must be between 1 and 10 characters"
    if not company_name or not company_name.strip():
        return None, "Company name is required"
    if not exchange or not exchange.strip():
        return None, "Exchange is required"
    
    existing = get_stock_by_ticker(ticker_clean)
    if existing:
        return None, f"Stock '{ticker_clean}' already exists"
    
    new_stock = create_stock(
        ticker=ticker_clean,
        company_name=company_name.strip(),
        exchange=exchange.strip(),
        sector=sector.strip() if sector else None
    )
    return new_stock, None


def create_new_observation_form(stock_id: int, observation_date: str,
                                timeframe: str, market_structure: Optional[str] = None,
                                setup_type: Optional[str] = "No Setup",
                                pattern: Optional[str] = None,
                                status: Optional[str] = "Watching",
                                key_observation: Optional[str] = None,
                                notes: Optional[str] = None,
                                trade_plan: Optional[Dict[str, Optional[float]]] = None,
                                levels: Optional[List[Dict[str, Any]]] = None):
    """Handle observation creation with optional Trade Plan and Support/Resistance levels."""
    if not stock_id:
        return None, "A stock must be selected"
    if not observation_date:
        return None, "Observation date is required"
    if not timeframe:
        return None, "Timeframe is required"
    
    st_val = setup_type if setup_type else "No Setup"
    stat_val = status if status else "Watching"
    tp = trade_plan or {}
    
    obs = create_observation(
        stock_id=stock_id,
        observation_date=str(observation_date),
        timeframe=timeframe,
        market_structure=market_structure.strip() if market_structure and market_structure.strip() else None,
        setup_type=st_val,
        pattern=pattern.strip() if pattern and pattern.strip() else None,
        status=stat_val,
        summary=None,
        key_observation=key_observation.strip() if key_observation and key_observation.strip() else None,
        notes=notes.strip() if notes and notes.strip() else None,
        entry_price_from=tp.get("entry_price_from"),
        entry_price_to=tp.get("entry_price_to"),
        stop_loss_from=tp.get("stop_loss_from"),
        stop_loss_to=tp.get("stop_loss_to"),
        target_price_from=tp.get("target_price_from"),
        target_price_to=tp.get("target_price_to"),
        levels=levels or []
    )
    return obs, None


def update_observation_form(observation_id: int,
                            observation_date: str,
                            timeframe: str,
                            market_structure: str,
                            setup_type: str,
                            pattern: str,
                            status: str,
                            key_observation: str,
                            notes: str,
                            trade_plan: Optional[Dict[str, Optional[float]]] = None,
                            levels: Optional[List[Dict[str, Any]]] = None,
                            status_notes: str = "Status updated"):
    """Handle complete update of an observation including Trade Plan and Levels."""
    tp = trade_plan or {}
    success = update_observation(
        observation_id=observation_id,
        observation_date=str(observation_date),
        timeframe=timeframe,
        market_structure=market_structure.strip() if market_structure else None,
        setup_type=setup_type,
        pattern=pattern.strip() if pattern else None,
        status=status,
        key_observation=key_observation.strip() if key_observation else None,
        notes=notes.strip() if notes else None,
        entry_price_from=tp.get("entry_price_from"),
        entry_price_to=tp.get("entry_price_to"),
        stop_loss_from=tp.get("stop_loss_from"),
        stop_loss_to=tp.get("stop_loss_to"),
        target_price_from=tp.get("target_price_from"),
        target_price_to=tp.get("target_price_to"),
        levels=levels,
        status_notes=status_notes
    )
    if success:
        return True, "Observation updated successfully"
    return False, "Failed to update observation"


def get_stock_detail_data(stock_id: int):
    """Get details for a stock and all its chronological observations."""
    stocks = get_stocks()
    stock = next((s for s in stocks if s.id == stock_id), None)
    if not stock:
        return None, []
    observations = get_stock_history(stock_id)
    return stock, observations


def get_observation_with_history(observation_id: int):
    """Get full observation details with price levels and status history."""
    return get_observation_by_id(observation_id)


def export_observations_to_csv(observations, filename: str = "observations_export.csv"):
    """Export complete observation data including Trade Plan and Chart Levels to CSV."""
    data = []
    for obs in observations:
        level_parts = []
        for l in (obs.levels or []):
            p_str = f"{l.price_from:g}"
            if l.price_to is not None and l.price_to != 0.0 and l.price_to != l.price_from:
                p_str += f"-{l.price_to:g}"
            lbl = l.label or l.level_type
            level_parts.append(f"{lbl}: {p_str}")
        levels_str = "; ".join(level_parts)
        
        entry_str = obs.get_price_range_str(obs.entry_price_from, obs.entry_price_to)
        sl_str = obs.get_price_range_str(obs.stop_loss_from, obs.stop_loss_to)
        tgt_str = obs.get_price_range_str(obs.target_price_from, obs.target_price_to)
        
        data.append({
            "Ticker": obs.stock_ticker or "N/A",
            "Company": obs.stock_name or "N/A",
            "Date": obs.observation_date,
            "Timeframe": obs.timeframe,
            "Setup Type": obs.setup_type,
            "Pattern": obs.pattern or "",
            "Market Structure": obs.market_structure or "",
            "Status": obs.status,
            "Entry": entry_str,
            "Stop Loss": sl_str,
            "Target": tgt_str,
            "Chart Levels": levels_str,
            "Key Observation": obs.key_observation or "",
            "Notes": obs.notes or ""
        })
    
    df = pd.DataFrame(data)
    export_path = f"data/{filename}"
    df.to_csv(export_path, index=False)
    return export_path
