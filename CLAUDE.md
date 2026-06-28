# TallySync — CLAUDE.md

Production-grade TallyPrime 7 synchronization agent built in Python 3.14 on Windows.
Reads accounting data from TallyPrime via HTTP/XML and syncs it to PostgreSQL.

---

## Project Status

### Completed phases

| Phase | Module | Status |
|-------|--------|--------|
| 0 | Scaffold — pyproject.toml, folder tree, .gitignore, alembic.ini | DONE |
| 1 | `app/config/settings.py` — Pydantic-settings + YAML + keyring | DONE |
| 1 | `app/logging/setup.py` — Loguru structured logging | DONE |
| 2 | `app/client/tally_client.py` — HTTP client, retry, streaming | DONE |
| 2 | `app/client/tally_health.py` — Health checker with cache | DONE |
| 2 | `tests/mock_tally/server.py` — Real TCP mock server | DONE |
| 3 | `app/xml/` — 12 XML request templates + `TemplateEngine` | DONE |
| 4 | `app/parser/` — lxml.iterparse parsers (8 entities) | DONE |
| 4 | `app/models/domain/` — Pydantic domain DTOs (8 records) | DONE |
| 5 | `app/models/db/` — SQLAlchemy ORM models (14 tables) + Alembic migration | DONE |
| 6 | `app/database/` — Engine factory, session scope, bulk upsert | DONE |
| 7 | `app/repositories/` — Abstract base + PostgreSQL implementations | DONE |
| 8 | `app/sync/` — SyncEngine, SyncResult, IteratorIO streaming helper | DONE |
| 9 | `app/services/` — BaseSyncService + 9 entity services (all entities) | DONE |
| 10 | `app/scheduler/` — TallySyncScheduler (APScheduler 3.x wrapper) | DONE |
| 11 | `app/parser/voucher.py` — Voucher parser (ledger/inventory/GST entries) | DONE |
| 11 | `app/models/domain/voucher.py` — VoucherRecord + sub-records | DONE |
| 11 | `app/repositories/postgres/voucher.py` — VoucherRepository (bulk upsert + child rows) | DONE |
| 12 | `app/api/` — FastAPI control API (localhost:8765) | DONE |
| 13 | `app/windows_service/` — pywin32 ServiceFramework + installer helpers | DONE |
| 14 | `tallysync.spec` + `install.ps1` — PyInstaller spec + PowerShell installer | DONE |
| 15 | `tests/unit/` — Tests for all new modules | DONE |

### All phases complete

```
All 15 phases implemented and passing.
```

---

## Architecture Decisions (approved, do not revisit)

1. **Database**: PostgreSQL (primary). MongoDB interface stub kept but not implemented.
2. **XML parsing**: `lxml.etree.iterparse()` streaming — NOT `xmltodict`. Never load full XML into memory.
3. **Incremental sync key**: Tally's `ALTERID` field — store max AlterID per entity per company in `sync_checkpoints` table.
4. **API separation**: Agent exposes only `http://127.0.0.1:8765` (localhost control). Cloud-facing REST API is a separate service reading from the DB.
5. **Windows Service**: `pywin32` ServiceFramework — no NSSM dependency.
6. **Scheduler**: APScheduler 3.x with `SQLAlchemyJobStore` — persists jobs across restarts.
7. **Development pace**: One module at a time. Every module must have passing tests and clean linter before moving to the next.

---

## Tech Stack

```
Python          3.14.6
pydantic        2.x  (domain models, DTOs)
pydantic-settings 2.x (config layer)
SQLAlchemy      2.x  (ORM + connection management)
alembic         1.x  (migrations)
psycopg         3.x  (PostgreSQL driver — NOT psycopg2)
lxml            6.x  (streaming XML parse)
requests        2.x  (HTTP client)
loguru          0.7  (structured logging)
APScheduler     3.x  (job scheduler)
fastapi         0.x  (internal control API)
pywin32         312  (Windows Service)
keyring         25.x (secrets via Windows Credential Manager)
click           8.x  (CLI)
tenacity        9.x  (available but manual retry loop used in client)
pytest          9.x  + pytest-asyncio, pytest-cov, responses, freezegun
ruff                 (lint + format)
mypy            2.x  (strict type checking)
```

Virtual environment: `.venv/` (Python 3.14, already created and populated)

---

## Configuration

- `config.yaml` — default config (no secrets)
- Env var prefix: `TALLYSYNC_`, nested delimiter `__`
  - Example: `TALLYSYNC_DATABASE__URL=postgresql+psycopg://...`
- Secrets stored in Windows Credential Manager via `keyring`
  - Service name: `tallysync`, username: `db_url`
- `Settings.from_yaml("config.yaml")` is the production entry point
- Direct `Settings(...)` kwargs construction is supported in tests

Priority order: `init kwargs > env vars > config.yaml > defaults`

---

## Coding Conventions

- All files use `from __future__ import annotations`
- Type hints everywhere — `mypy --strict` must pass
- No comments explaining WHAT code does — only WHY (non-obvious constraints)
- `loguru` logger: `from loguru import logger` — structured key=value args
- Tests use `MockTallyServer` (real TCP server, random port) — no `responses` mocking for HTTP
- Run `ruff check --fix` and `ruff format` after every file
- All tests must pass before moving to the next phase

---

## Tally XML API

- Endpoint: `POST http://localhost:9000`
- Content-Type: `text/xml;charset=utf-8`
- Tally returns HTTP 200 even for errors — always check `<STATUS>1</STATUS>` or `<LINEERROR>` in body
- AlterID: global monotonic counter in Tally; use `ALTERID > last_known` for incremental sync
- Large responses: use `stream_request()` → `lxml.iterparse` pipeline

### Entity sync order (FK dependency order)
```
1. company          (no deps)
2. ledger_group     (self-referential tree — parent before child)
3. unit             (no deps)
4. stock_group      (self-referential tree)
5. godown           (no deps)
6. voucher_type     (no deps)
7. stock_item       (depends on stock_group, unit)
8. ledger           (depends on ledger_group)
9. voucher          (depends on everything above)
```

---

## Database Schema (key tables)

```sql
sync_checkpoints  -- last_alter_id per (company_name, entity_type)
sync_runs         -- audit log of every sync execution
ledger_groups     -- tree structure, company-scoped
ledgers           -- party master (customers, suppliers, banks, etc.)
vouchers          -- header: number, date, type, party, narration
voucher_items     -- line items (debit/credit legs)
gst_details       -- HSN, IGST, CGST, SGST per voucher
stock_items       -- inventory master
stock_groups      -- tree
godowns           -- warehouse/location
units             -- unit of measure
```

Natural keys for upsert:
- Voucher: `(company_name, voucher_number, voucher_type)`
- Ledger: `(company_name, name)`
- StockItem: `(company_name, name)`

---

## Key Files

```
app/main.py               CLI entry point (click)
app/agent.py              Composition root (wires all modules)
app/config/settings.py    Root Settings + YAML source + keyring
app/logging/setup.py      Loguru sink configuration
app/client/tally_client.py  HTTP client (retry, stream, error detection)
app/client/tally_health.py  Health checker with TTL cache
tests/mock_tally/server.py  In-process mock HTTP server for tests
tests/conftest.py           Shared fixtures: test_settings, mock_tally
```

---

## Running Tests

```powershell
# All unit tests
.venv\Scripts\pytest tests\unit\ --no-cov -v

# With coverage
.venv\Scripts\pytest tests\unit\ --cov=app --cov-report=term-missing

# Single module
.venv\Scripts\pytest tests\unit\test_tally_client.py -v
```

## Linting

```powershell
.venv\Scripts\ruff check --fix app\
.venv\Scripts\ruff format app\
```

---

## Test Results Snapshot

```
Phase 0+1 (settings, logging):  13/13 passing
Phase 2   (client, health):     28/28 passing
Phase 3   (xml templates):      33/33 passing
Phase 4   (parsers + models):   81/81 passing
Phase 5-7  (db models, db layer, repos):    53/53 passing
Phase 8-15 (sync, services, api, parser):   38/38 passing
Total:                                     262/262 passing
```
