# Architecture v1.1 for Phase 0

## 1. Architecture Overview

**Browser (Next.js)** → **FastAPI (HTTP)** → **Business Layer (Pure Python)** → **Persistence Layer (SQLite only)**

- Next.js: React app with pages (watchlist, dashboard)
- FastAPI: REST endpoints only; no business logic
- Business: Pure Python; contains calculations, validation, Excel parsing, business rules
- Persistence: SQLite wrapper; contains sqlite3 and SQL queries only
- SQLite: Single file, local storage

**No interfaces, no dependency injection, no abstract repositories.** Business calls persistence functions directly.

---

## 2. Component Boundaries

| Layer | Responsibility | Dependencies |
|-------|---------------|--------------|
| **Next.js** | React pages, state, table rendering | None (client-only) |
| **FastAPI** | HTTP transport: routes, request/response models | `pydantic`, `fastapi` |
| **Business** | Excel parsing, calculations, validation, orchestration | Only `pandas` (optional), Python stdlib |
| **Persistence** | sqlite3 and SQL queries only | `sqlite3` only |
| **Storage** | Local filesystem (no S3/external) | `os`, `pathlib` only |

**Key boundary:** Business layer must NOT import or depend on `sqlite3`.

---

## 3. Data Model

### Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `stocks` | Watchlist | `id`, `symbol`, `name`, `created_at`, `is_active` |
| `levels` | Support/resistance history | `id`, `stock_id`, `level_type`, `level_order`, `level_value`, `recorded_at` |
| `observations` | Journal notes | `id`, `stock_id`, `content`, `recorded_at` |
| `snapshots` | Market data history | `id`, `stock_id`, `snapshot_date`, `price`, `dma50`, `dma200`, `prev_volume`, `avg_30d_volume`, `uploaded_at` |

**Indexes:**
- `stocks(symbol, is_active)`
- `levels(stock_id, level_type, level_order, recorded_at DESC)`
- `observations(stock_id, recorded_at DESC)`
- `snapshots(stock_id, snapshot_date DESC)`

---

## 4. Support/Resistance Level History

**Design:**
- Exactly 3 support slots and 3 resistance slots.
- `level_order` = slot number (1, 2, 3).
- Each change creates a NEW row; no UPDATE/DELETE.
- Current level = **latest row per `(stock_id, level_type, level_order)`**.

**Clearing a level:**
- To remove Support 1: `INSERT INTO levels (stock_id, 'support', 1, NULL, 'now')`.
- This preserves history; the slot is now empty.

**Query for current level:**
```sql
SELECT * FROM levels 
WHERE stock_id=? AND level_type=? AND level_order=?
ORDER BY recorded_at DESC LIMIT 1
```

**Example:**
- Support 1 on Jan 1: `{100}`
- Support 1 on Jan 15: `{102}`
- Support 1 on Jan 24: `{105}` (current)

All three rows exist. Latest per slot is the current value.

---

## 5. Exact Calculation Definitions

**Denominator = reference value** for all formulas.

| Metric | Formula | Direction |
|--------|---------|-----------|
| **Support dist** | `(price - support) / support * 100` | `+` = price above support |
| **Resistance dist** | `(resistance - price) / resistance * 100` | `+` = price below resistance, `–` = above |
| **50 DMA dist** | `(price - dma50) / dma50 * 100` | `+` = above, `–` = below |
| **200 DMA dist** | `(price - dma200) / dma200 * 100` | `+` = above, `–` = below |
| **Volume vs 30D** | `(prev_volume - avg_30d_volume) / avg_30d_volume * 100` | `+` = higher volume |

**Edge cases:**
- No support/resistance = `null`
- Price below all supports → use lowest support for distance
- Price above all resistances → use highest resistance for distance

---

## 6. Nearest Support/Resistance

**Definition:** Level with smallest **absolute price distance** from current price, subject to availability.

**Algorithm:**
1. Collect all supports below price; if empty, use lowest support.
2. Collect all resistances above price; if empty, use highest resistance.
3. Pick support/resistance with `abs(price - level)` minimized.

**Examples:**
- Price = ₹100, Supports = [90, 95] → nearest = 95 (`|100-95|=5`)
- Price = ₹100, Resistances = [105, 110] → nearest = 105 (`|105-100|=5`)
- Price = ₹80, Supports = [90, 95] → nearest = 90 (lowest support)

**Edge case:** If both support and resistance missing, distance = `null`.

---

## 7. Excel Ingestion & Watchlist

**Watchlist is source of truth.**

**Flow:**
1. Upload Excel file.
2. For each row symbol:
   - If exists in active watchlist → ingest snapshot.
   - If not → skip and report as unknown symbol.
3. Snapshot date = ingestion date (no Excel date column required).
4. No new stocks created silently.

**Rationale:** User must explicitly add stocks to watchlist first; Excel ingestion adds market data only to known stocks.

---

## 8. Persistence Boundary (Lightweight)

**Persistence owns sqlite3 and SQL. Business does NOT import sqlite3.**

```python
# persistence/sqlite.py (only file importing sqlite3)
def get_connection():
    return sqlite3.connect("data/trading.db")

def save_level(conn, stock_id, level_type, level_order, level_value):
    conn.execute("INSERT INTO levels ...", (stock_id, level_type, level_order, level_value, ...))

def get_current_levels(conn, stock_id, level_type):
    return conn.execute("""
        SELECT * FROM levels 
        WHERE stock_id=? AND level_type=? 
        ORDER BY recorded_at DESC LIMIT 1
    """, (stock_id, level_type)).fetchall()
```

**Business calls:**
```python
# domain/services.py
def add_level(stock_id, level_type, level_order, level_value):
    conn = persistence.get_connection()
    persistence.save_level(conn, stock_id, level_type, level_order, level_value)
    # no sqlite3 import here
```

**No interfaces, no factories, no dependency injection.**

---

## 9. Docker/local Architecture

**Two containers (dev):**

- **Backend**: FastAPI on port `8000`
- **Frontend**: Next.js on port `3000`

**SQLite location:**
- Backend Docker volume: `- ./data:/app/data`
- File: `/app/data/trading.db`

**No external DB services.** SQLite is embedded in backend container.

---

## 10. UI Structure

### Pages

**`/watchlist`**
- Add/edit stock (symbol, name)
- Edit 3 support slots, 3 resistance slots
- Journal notes textarea

**`/dashboard`**
- Excel upload
- Filter checkboxes: `Near support`, `Near resistance`, `Near 50 DMA`, `Near 200 DMA`, `Volume > X%`
- Configurable threshold inputs (2% default)
- Table columns (primary first):
  1. Symbol
  2. Dist to 50 DMA %
  3. Dist to 200 DMA %
  4. Dist to Nearest Support %
  5. Dist to Nearest Resistance %
  6. Volume vs 30D %
  7. Latest note
- Expandable context row for price, DMA, support/resistance prices, volumes.

**No volume spike logic.** Volume remains continuous %.

---

## 11. Repository Structure

```
swing/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints
│   │   │   └── routes/
│   │   ├── domain/           # Pure Python (NO sqlite3)
│   │   │   ├── entities.py
│   │   │   ├── excel_loader.py
│   │   │   ├── calculator.py
│   │   │   └── services.py
│   │   └── persistence/      # SQLite + SQL only
│   │       ├── sqlite.py
│   │       ├── stock_queries.py
│   │       ├── level_queries.py
│   │       └── ...
│   └── tests/
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── watchlist/
│   │   └── dashboard/
│   ├── components/
│   └── lib/
├── data/                     # SQLite file (ignored in git)
├── db/
│   └── schema.sql
├── docs/
│   ├── architecture.md
│   └── decisions/
├── docker-compose.yml
├── .gitignore
├── .env.example
└── README.md
```

---

## 12. Future Extensibility

**Principle:** New modules added as independent tables referencing `stocks(id)`.

**Example modules:**
- `fundamentals(stock_id, revenue, eps, pe_ratio, ...)`
- `earnings(stock_id, report_date, eps_actual, ...)`
- `news(stock_id, date, headline, source)`
- `technical_indicators(stock_id, date, rsi, macd, ...)`
- `ai_analysis(stock_id, date, summary, sentiment)`

**No guarantee of zero disruption.** Future modules may require schema changes (e.g., new columns, indexes). The architecture is designed to **minimize disruption to Phase 0 core**, not to prevent all future changes.

---

## 13. Risks

| Risk | Mitigation | Severity |
|------|------------|----------|
| **level-history correctness** | Testing: verify latest row per `(stock_id, level_type, level_order)` returns current value | Medium (catch in tests) |
| **Excel symbols not matching watchlist** | Validation layer; unknown symbols rejected | Low (user education) |
| **Snapshot-date semantics** | Use ingestion date; no Excel date column | Low (documented) |
| **Input data validation/integrity** | Strict Excel column validation; type checks | Medium (data quality) |
| **SQLite concurrency** | Single-user phase; <100 stocks | Low (Phase 0 scope) |
| **Excel format drift** | Column validation with clear error messages | Low (user education) |

---

## 14. Final Recommendation

**Frontend**: Next.js + TypeScript (React, app router, TypeScript)

**Backend**: FastAPI + Python business logic

**Database**: SQLite (embedded, file-based)

**Storage**: Local filesystem only; no S3

**Containerization**: Two-container Docker Compose (backend + frontend)

**Persistence boundary**: Lightweight; persistence owns sqlite3, business does not import it

**Key:**
- Business layer: pure Python (no sqlite3)
- Persistence: sqlite3 and SQL only
- No enterprise patterns (no interfaces, no DI, no factories)

**This is Phase 0. Scope is small, deployable, and extensible.**
