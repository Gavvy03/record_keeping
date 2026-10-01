from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from persistence.database import (
    get_connection, init_db, seed_demo_data,
    update_observation_status, get_price_levels_by_observation_ids
)


VALID_TIMEFRAMES = ["Weekly", "Daily", "4H", "1H"]
VALID_SETUP_TYPES = ["No Setup", "Breakout", "Breakdown", "Reversal", "Pullback", 
                     "Continuation", "Range"]
VALID_STATUSES = ["Watching", "Triggered", "Confirmed", "Failed", "Expired"]
VALID_LEVEL_TYPES = ["Support", "Resistance", "Breakout Trigger", 
                     "Breakdown Trigger", "Invalidation", "Target"]
VALID_PRIORITIES = ["High", "Medium", "Low"]


@dataclass
class Stock:
    id: Optional[int]
    ticker: str
    company_name: str
    exchange: str
    sector: Optional[str] = None
    
    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            ticker=row["ticker"],
            company_name=row["company_name"],
            exchange=row["exchange"],
            sector=row["sector"]
        )


@dataclass
class PriceLevel:
    id: Optional[int]
    observation_id: int
    level_type: str
    label: Optional[str]
    price_from: float
    price_to: Optional[float]
    priority: Optional[str]
    notes: Optional[str]
    
    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            observation_id=row["observation_id"],
            level_type=row["level_type"],
            label=row["label"],
            price_from=row["price_from"],
            price_to=row["price_to"],
            priority=row["priority"],
            notes=row["notes"]
        )


@dataclass
class ChartObservation:
    id: Optional[int]
    stock_id: int
    observation_date: str
    timeframe: str
    market_structure: Optional[str]
    setup_type: str
    pattern: Optional[str]
    status: str
    summary: Optional[str]
    key_observation: Optional[str]
    notes: Optional[str]
    created_at: Optional[str] = None
    entry_price_from: Optional[float] = None
    entry_price_to: Optional[float] = None
    stop_loss_from: Optional[float] = None
    stop_loss_to: Optional[float] = None
    target_price_from: Optional[float] = None
    target_price_to: Optional[float] = None
    stock_ticker: Optional[str] = None
    stock_name: Optional[str] = None
    levels: list = None
    history: list = None
    
    def __post_init__(self):
        if self.levels is None:
            self.levels = []
        if self.history is None:
            self.history = []
    
    @classmethod
    def from_row(cls, row):
        keys = row.keys() if hasattr(row, "keys") else []
        return cls(
            id=row["id"] if "id" in keys else None,
            stock_id=row["stock_id"] if "stock_id" in keys else None,
            observation_date=row["observation_date"] if "observation_date" in keys else "",
            timeframe=row["timeframe"] if "timeframe" in keys else "",
            market_structure=row["market_structure"] if "market_structure" in keys else None,
            setup_type=row["setup_type"] if "setup_type" in keys else "",
            pattern=row["pattern"] if "pattern" in keys else None,
            status=row["status"] if "status" in keys else "",
            summary=row["summary"] if "summary" in keys else None,
            key_observation=row["key_observation"] if "key_observation" in keys else None,
            notes=row["notes"] if "notes" in keys else None,
            created_at=row["created_at"] if "created_at" in keys else None,
            entry_price_from=row["entry_price_from"] if "entry_price_from" in keys else None,
            entry_price_to=row["entry_price_to"] if "entry_price_to" in keys else None,
            stop_loss_from=row["stop_loss_from"] if "stop_loss_from" in keys else None,
            stop_loss_to=row["stop_loss_to"] if "stop_loss_to" in keys else None,
            target_price_from=row["target_price_from"] if "target_price_from" in keys else None,
            target_price_to=row["target_price_to"] if "target_price_to" in keys else None,
            stock_ticker=row["stock_ticker"] if "stock_ticker" in keys else (row["ticker"] if "ticker" in keys else None),
            stock_name=row["stock_name"] if "stock_name" in keys else (row["company_name"] if "company_name" in keys else None),
        )

    def get_price_range_str(self, price_from, price_to):
        """Format single price or price range string."""
        if price_from is None:
            return "-"
        if price_to is not None and price_to != 0.0 and price_to != price_from:
            return f"{price_from:g} – {price_to:g}"
        return f"{price_from:g}"

    def get_trade_plan_summary(self):
        """Get compact summary string for Trade Plan."""
        parts = []
        if self.entry_price_from is not None:
            parts.append(f"Entry: {self.get_price_range_str(self.entry_price_from, self.entry_price_to)}")
        if self.stop_loss_from is not None:
            parts.append(f"SL: {self.get_price_range_str(self.stop_loss_from, self.stop_loss_to)}")
        if self.target_price_from is not None:
            parts.append(f"Target: {self.get_price_range_str(self.target_price_from, self.target_price_to)}")
        return " | ".join(parts) if parts else "—"

    def get_levels_dict(self):
        """Map levels into fixed Support 1..3 and Resistance 1..3 slots."""
        data = {
            "Support 1": None, "Support 2": None, "Support 3": None,
            "Resistance 1": None, "Resistance 2": None, "Resistance 3": None,
        }
        supports = [l for l in (self.levels or []) if l.level_type == "Support"]
        resistances = [l for l in (self.levels or []) if l.level_type == "Resistance"]
        
        # Exact labels first
        used_s = set()
        for l in supports:
            if l.label in data and data[l.label] is None:
                data[l.label] = l
                used_s.add(id(l))
        for l in supports:
            if id(l) not in used_s:
                for slot in ["Support 1", "Support 2", "Support 3"]:
                    if data[slot] is None:
                        data[slot] = l
                        break

        used_r = set()
        for l in resistances:
            if l.label in data and data[l.label] is None:
                data[l.label] = l
                used_r.add(id(l))
        for l in resistances:
            if id(l) not in used_r:
                for slot in ["Resistance 1", "Resistance 2", "Resistance 3"]:
                    if data[slot] is None:
                        data[slot] = l
                        break
        return data


def init_database():
    """Initialize database and seed demo data if empty."""
    init_db()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        count = cursor.fetchone()[0]
        if count == 0:
            seed_demo_data()
    finally:
        conn.close()


def validate_ticker(ticker: str) -> bool:
    """Validate stock ticker format."""
    return len(ticker) > 0 and len(ticker) <= 10


def validate_price(price: float) -> bool:
    """Validate price is positive."""
    return price > 0


def validate_setup_type(setup_type: str) -> bool:
    """Validate setup type."""
    return setup_type in VALID_SETUP_TYPES


def validate_status(status: str) -> bool:
    """Validate status."""
    return status in VALID_STATUSES


def validate_timeframe(timeframe: str) -> bool:
    """Validate timeframe."""
    return timeframe in VALID_TIMEFRAMES


def validate_level_type(level_type: str) -> bool:
    """Validate price level type."""
    return level_type in VALID_LEVEL_TYPES


def validate_priority(priority: str) -> bool:
    """Validate priority."""
    return priority in VALID_PRIORITIES


def get_stocks():
    """Get all stocks."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stocks ORDER BY ticker")
        return [Stock.from_row(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_stock_by_ticker(ticker: str):
    """Get stock by ticker."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stocks WHERE ticker = ?", (ticker,))
        row = cursor.fetchone()
        return Stock.from_row(row) if row else None
    finally:
        conn.close()


def create_stock(ticker: str, company_name: str, exchange: str, 
                 sector: Optional[str] = None) -> Stock:
    """Create a new stock."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stocks (ticker, company_name, exchange, sector)
            VALUES (?, ?, ?, ?)
        """, (ticker, company_name, exchange, sector))
        conn.commit()
        
        cursor.execute("SELECT * FROM stocks WHERE id = ?", (cursor.lastrowid,))
        return Stock.from_row(cursor.fetchone())
    finally:
        conn.close()


def get_chart_observations(stock_id: Optional[int] = None,
                           status: Optional[str] = None,
                           setup_type: Optional[str] = None,
                           pattern: Optional[str] = None,
                           market_structure: Optional[str] = None,
                           date_from: Optional[str] = None,
                           date_to: Optional[str] = None,
                           search_text: Optional[str] = None):
    """Get chart observations with rich filters, stock details joined, and batch levels."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT co.*, s.ticker AS stock_ticker, s.company_name AS stock_name
            FROM chart_observations co
            JOIN stocks s ON co.stock_id = s.id
            WHERE 1=1
        """
        params = []
        
        if stock_id:
            query += " AND co.stock_id = ?"
            params.append(stock_id)
        
        if status and status != "All":
            query += " AND co.status = ?"
            params.append(status)
        
        if setup_type and setup_type != "All":
            query += " AND co.setup_type = ?"
            params.append(setup_type)
        
        if pattern:
            query += " AND LOWER(co.pattern) LIKE ?"
            params.append(f"%{pattern.lower()}%")
        
        if market_structure and market_structure != "All":
            query += " AND LOWER(co.market_structure) LIKE ?"
            params.append(f"%{market_structure.lower()}%")
        
        if date_from:
            query += " AND co.observation_date >= ?"
            params.append(str(date_from))
        
        if date_to:
            query += " AND co.observation_date <= ?"
            params.append(str(date_to))
        
        if search_text:
            query += " AND (LOWER(co.key_observation) LIKE ? OR LOWER(co.notes) LIKE ?)"
            st_param = f"%{search_text.lower()}%"
            params.extend([st_param, st_param])
        
        query += " ORDER BY co.observation_date DESC, co.created_at DESC"
        
        cursor.execute(query, params)
        observations = [ChartObservation.from_row(row) for row in cursor.fetchall()]
        
        # Batch load price levels to eliminate N+1 queries
        if observations:
            obs_ids = [obs.id for obs in observations if obs.id]
            levels_by_obs = get_price_levels_by_observation_ids(conn, obs_ids)
            for obs in observations:
                obs.levels = [PriceLevel.from_row(row) for row in levels_by_obs.get(obs.id, [])]
        
        return observations
    finally:
        conn.close()


def get_observation_by_id(observation_id: int) -> Optional[ChartObservation]:
    """Get a single observation by ID with stock info, price levels, and status history."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT co.*, s.ticker AS stock_ticker, s.company_name AS stock_name
            FROM chart_observations co
            JOIN stocks s ON co.stock_id = s.id
            WHERE co.id = ?
        """, (observation_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        obs = ChartObservation.from_row(row)
        
        cursor.execute("""
            SELECT * FROM price_levels 
            WHERE observation_id = ?
            ORDER BY level_type, label, price_from
        """, (observation_id,))
        obs.levels = [PriceLevel.from_row(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT * FROM observation_history 
            WHERE observation_id = ?
            ORDER BY changed_at DESC, id DESC
        """, (observation_id,))
        obs.history = [dict(row) for row in cursor.fetchall()]
        
        return obs
    finally:
        conn.close()


def create_observation(stock_id: int, observation_date: str, timeframe: str,
                       market_structure: Optional[str] = None,
                       setup_type: str = "No Setup",
                       pattern: Optional[str] = None,
                       status: str = "Watching",
                       summary: Optional[str] = None,
                       key_observation: Optional[str] = None,
                       notes: Optional[str] = None,
                       entry_price_from: Optional[float] = None,
                       entry_price_to: Optional[float] = None,
                       stop_loss_from: Optional[float] = None,
                       stop_loss_to: Optional[float] = None,
                       target_price_from: Optional[float] = None,
                       target_price_to: Optional[float] = None,
                       levels: Optional[list] = None) -> ChartObservation:
    """Create a new chart observation with optional Trade Plan and Chart Levels."""
    obs = ChartObservation(
        id=None,
        stock_id=stock_id,
        observation_date=observation_date,
        timeframe=timeframe,
        market_structure=market_structure,
        setup_type=setup_type,
        pattern=pattern,
        status=status,
        summary=summary,
        key_observation=key_observation,
        notes=notes,
        entry_price_from=entry_price_from,
        entry_price_to=entry_price_to,
        stop_loss_from=stop_loss_from,
        stop_loss_to=stop_loss_to,
        target_price_from=target_price_from,
        target_price_to=target_price_to,
        levels=[]
    )
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chart_observations 
            (stock_id, observation_date, timeframe, market_structure, 
             setup_type, pattern, status, summary, key_observation, notes,
             entry_price_from, entry_price_to, stop_loss_from, stop_loss_to,
             target_price_from, target_price_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (obs.stock_id, obs.observation_date, obs.timeframe, 
              obs.market_structure, obs.setup_type, obs.pattern, 
              obs.status, obs.summary, obs.key_observation, obs.notes,
              obs.entry_price_from, obs.entry_price_to,
              obs.stop_loss_from, obs.stop_loss_to,
              obs.target_price_from, obs.target_price_to))
        obs.id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO observation_history (observation_id, status, notes)
            VALUES (?, ?, ?)
        """, (obs.id, obs.status, "Observation created"))
        
        if levels:
            for lvl in levels:
                if isinstance(lvl, dict):
                    level_type = lvl.get("level_type")
                    label = lvl.get("label")
                    price_from = lvl.get("price_from")
                    price_to = lvl.get("price_to")
                    priority = lvl.get("priority")
                    l_notes = lvl.get("notes")
                else:
                    level_type = getattr(lvl, "level_type")
                    label = getattr(lvl, "label")
                    price_from = getattr(lvl, "price_from")
                    price_to = getattr(lvl, "price_to", None)
                    priority = getattr(lvl, "priority", None)
                    l_notes = getattr(lvl, "notes", None)
                if price_from is not None and price_from > 0:
                    cursor.execute("""
                        INSERT INTO price_levels 
                        (observation_id, level_type, label, price_from, price_to, priority, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (obs.id, level_type, label, price_from, price_to, priority, l_notes))
                    obs.levels.append(PriceLevel(
                        id=cursor.lastrowid,
                        observation_id=obs.id,
                        level_type=level_type,
                        label=label,
                        price_from=price_from,
                        price_to=price_to,
                        priority=priority,
                        notes=l_notes
                    ))
        
        conn.commit()
        return obs
    finally:
        conn.close()


def update_observation(observation_id: int, **kwargs) -> bool:
    """Update an existing observation including Trade Plan and Chart Levels."""
    allowed_fields = [
        "observation_date", "timeframe", "market_structure",
        "setup_type", "pattern", "status", "summary", 
        "key_observation", "notes",
        "entry_price_from", "entry_price_to",
        "stop_loss_from", "stop_loss_to",
        "target_price_from", "target_price_to"
    ]
    
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    levels_to_save = kwargs.get("levels", None)
    
    if not updates and levels_to_save is None:
        return False
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        if updates:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), observation_id]
            
            cursor.execute(f"""
                UPDATE chart_observations 
                SET {set_clause}, updated_at = ?
                WHERE id = ?
            """, values)
            
            if "status" in updates:
                status_notes = kwargs.get("status_notes", "Status updated")
                cursor.execute("""
                    INSERT INTO observation_history (observation_id, status, notes)
                    VALUES (?, ?, ?)
                """, (observation_id, updates["status"], status_notes))
        
        if levels_to_save is not None:
            cursor.execute("DELETE FROM price_levels WHERE observation_id = ?", (observation_id,))
            for lvl in levels_to_save:
                if isinstance(lvl, dict):
                    level_type = lvl.get("level_type")
                    label = lvl.get("label")
                    price_from = lvl.get("price_from")
                    price_to = lvl.get("price_to")
                    priority = lvl.get("priority")
                    l_notes = lvl.get("notes")
                else:
                    level_type = getattr(lvl, "level_type")
                    label = getattr(lvl, "label")
                    price_from = getattr(lvl, "price_from")
                    price_to = getattr(lvl, "price_to", None)
                    priority = getattr(lvl, "priority", None)
                    l_notes = getattr(lvl, "notes", None)
                if price_from is not None and price_from > 0:
                    cursor.execute("""
                        INSERT INTO price_levels 
                        (observation_id, level_type, label, price_from, price_to, priority, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (observation_id, level_type, label, price_from, price_to, priority, l_notes))
        
        conn.commit()
        return True
    finally:
        conn.close()


def get_stock_history(stock_id: int):
    """Get all observations for a stock ordered chronologically newest first."""
    return get_chart_observations(stock_id=stock_id)


def create_price_level(observation_id: int, level_type: str, label: Optional[str],
                       price_from: float, price_to: Optional[float],
                       priority: Optional[str], notes: Optional[str]) -> PriceLevel:
    """Create a new price level."""
    level = PriceLevel(
        id=None,
        observation_id=observation_id,
        level_type=level_type,
        label=label,
        price_from=price_from,
        price_to=price_to,
        priority=priority,
        notes=notes
    )
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO price_levels 
            (observation_id, level_type, label, price_from, price_to, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (level.observation_id, level.level_type, level.label,
              level.price_from, level.price_to, level.priority, level.notes))
        level.id = cursor.lastrowid
        conn.commit()
        return level
    finally:
        conn.close()


def update_price_level(level_id: int, **kwargs) -> bool:
    """Update an existing price level."""
    allowed_fields = ["level_type", "label", "price_from", "price_to",
                      "priority", "notes"]
    
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [level_id]
        cursor.execute(f"""
            UPDATE price_levels 
            SET {set_clause}
            WHERE id = ?
        """, values)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_price_level(level_id: int) -> bool:
    """Delete a price level."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM price_levels WHERE id = ?", (level_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_observation_status_history(observation_id: int):
    """Get status change history for an observation."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM observation_history 
            WHERE observation_id = ?
            ORDER BY changed_at DESC, id DESC
        """, (observation_id,))
        return cursor.fetchall()
    finally:
        conn.close()


def get_observations_by_stock(stock_id: int):
    """Get all observations for a stock."""
    return get_chart_observations(stock_id=stock_id)


def get_observations_counts_by_status():
    """Get count of observations grouped by status."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM chart_observations 
            GROUP BY status 
            ORDER BY count DESC
        """)
        return cursor.fetchall()
    finally:
        conn.close()


def get_recent_observations(limit: int = 10):
    """Get most recent observations."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT co.*, s.ticker, s.company_name 
            FROM chart_observations co
            JOIN stocks s ON co.stock_id = s.id
            ORDER BY co.observation_date DESC, co.created_at DESC
            LIMIT ?
        """, (limit,))
        observations = []
        for row in cursor.fetchall():
            obs = ChartObservation.from_row(row)
            obs.stock_ticker = row["ticker"]
            obs.stock_name = row["company_name"]
            observations.append(obs)
        return observations
    finally:
        conn.close()


def get_all_timeframes():
    """Get valid timeframes."""
    return VALID_TIMEFRAMES.copy()


def get_all_setup_types():
    """Get valid setup types."""
    return VALID_SETUP_TYPES.copy()


def get_all_statuses():
    """Get valid statuses."""
    return VALID_STATUSES.copy()


def get_all_level_types():
    """Get valid level types."""
    return VALID_LEVEL_TYPES.copy()


def get_all_priorities():
    """Get valid priorities."""
    return VALID_PRIORITIES.copy()
