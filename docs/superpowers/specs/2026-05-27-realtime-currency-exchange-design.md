# Real-Time Currency Exchange — Design Spec

**Date:** 2026-05-27
**Status:** Approved

## 1. Purpose & Scope

A containerized web app that displays **live foreign-exchange rates** that stream to all
connected clients in real time, plus a **currency converter**. It is **view-only**: no user
accounts, wallets, or transactions.

Rates are sourced by polling a **free forex API** (Frankfurter / ECB) on a schedule; each poll
is broadcast over websockets to connected browsers. Every poll is also persisted as a
time-series snapshot, enabling **historical charts**.

In scope:
- Live, auto-updating rates board (pushed via websocket).
- Currency converter (instant, computed client-side from latest rates).
- Historical rate charts (e.g. EUR/USD over 24h).

Out of scope (YAGNI):
- Authentication / user accounts.
- Wallets, balances, buy/sell transactions.
- Rate alerts / notifications.
- Web scraping (the `scrapers/` folder is repurposed as the API fetcher module).

## 2. Architecture — Container Topology

Orchestrated via `docker-compose`. All configuration comes from a single root `.env`.

| Service | Image / Base | Role |
|---|---|---|
| `postgres` | postgres:16 | Rate history + currency metadata |
| `redis` | redis:7 | Channels layer + cache + Celery broker & result backend |
| `backend` | python:3.12 | Django + Channels (ASGI), served by **uvicorn**; HTTP REST + websockets |
| `celery-worker` | python:3.12 | Runs the `fetch_rates` task |
| `celery-beat` | python:3.12 | Schedules `fetch_rates` every `POLL_INTERVAL_SECONDS` |
| `frontend` | node:20 build → nginx | React (Vite) build served by **nginx**; reverse-proxies `/api` and `/ws` to `backend` |

`backend`, `celery-worker`, and `celery-beat` share the same image/code; they differ only by
their start command.

## 3. Backend (Django)

- Django project `config/`, single app `rates/`.
- Settings loaded from `.env` via `django-environ`.
- ASGI entrypoint runs under **uvicorn**; Channels routes websockets, Django handles HTTP.

### 3.1 Models
- `Currency(code, name, symbol)` — e.g. `("USD", "US Dollar", "$")`. `code` is the PK/unique.
- `ExchangeRate(base FK→Currency, quote FK→Currency, rate Decimal, fetched_at datetime)` —
  one row per currency pair per poll → time-series history. Indexed on
  `(base, quote, fetched_at)` for history queries and on `fetched_at` for latest lookups.

### 3.2 Fetcher (repurposed `scrapers/`)
- A typed client module wrapping the free forex API (Frankfurter; base = configurable, default
  EUR from ECB).
- Returns a normalized structure: base currency + `{quote_code: rate}` + timestamp.
- Cross-rates for arbitrary pairs (e.g. USD→GBP) are computed from the common base.
- Network calls isolated behind one function so tests can mock it.

### 3.3 Background polling (Celery)
- `celery-beat` schedules task `fetch_rates` every `POLL_INTERVAL_SECONDS` (default 10).
- `fetch_rates` (run by `celery-worker`): call fetcher → bulk-insert `ExchangeRate` snapshot
  rows → `group_send` the latest rate set to Channels group `rates`.

### 3.4 Websockets (Channels)
- `RatesConsumer` at `/ws/rates/`:
  - On connect: join group `rates`, send the current latest snapshot immediately.
  - On group broadcast: relay latest rates to the client as JSON.
- Channel layer backed by Redis (`channels_redis`).

### 3.5 REST API (DRF)
- `GET /api/currencies/` — list supported currencies.
- `GET /api/rates/latest/` — latest snapshot for all pairs (initial page load fallback).
- `GET /api/rates/history/?base=&quote=&range=24h` — time-series for charts.
- `GET /api/convert/?from=&to=&amount=` — server-side conversion (validation/fallback).

## 4. Frontend (React + Redux Toolkit, Vite)

- Vite-built React app, served as static files by nginx in production.
- **Redux Toolkit** store with slices: `currencies`, `liveRates`, `converter`, `history`.
- **WebSocket middleware**: connects to `/ws/rates/`, dispatches incoming rate updates into the
  `liveRates` slice; handles reconnect with backoff.
- Initial / non-streaming data via **RTK Query** (or fetch): currencies, history, latest.
- Components:
  - **LiveRatesBoard** — table of pairs that updates live as websocket messages arrive.
  - **Converter** — pick from/to + amount; computed instantly from in-store latest rates.
  - **HistoryChart** — Recharts line chart of a selected pair over a time range.

## 5. Data Flow

```
Celery Beat ──schedule──▶ fetch_rates (worker)
                              │
                fetcher ──▶ forex API
                              │
              ┌───────────────┴───────────────┐
              ▼                                ▼
        Postgres (snapshot)          Redis group_send "rates"
                                              │
                                       RatesConsumer (/ws/rates/)
                                              │
                                     all connected browsers
                                              │
                                     RTK liveRates slice ──▶ UI re-render
```

The converter reads the latest rates already in the RTK store, so conversions are instant and
need no round-trip. `/api/convert` exists as a server-side fallback / validation path.

## 6. Configuration (`.env`)

Single root `.env` consumed by docker-compose for all services. Keys (sample in `.env.sample`):

- Django: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- Postgres: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- Redis: `REDIS_URL`
- Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- App: `FOREX_API_BASE_URL`, `BASE_CURRENCY` (default EUR), `POLL_INTERVAL_SECONDS` (default 10),
  `SUPPORTED_CURRENCIES`
- Frontend: `VITE_API_URL`, `VITE_WS_URL`

## 7. Testing

- **Backend** (`pytest-django`):
  - Fetcher with mocked API responses (incl. error/timeout handling).
  - Conversion math (cross-rates, rounding).
  - Models & history queries.
  - `fetch_rates` Celery task (mock fetcher; assert DB rows + broadcast).
  - `RatesConsumer` via Channels `WebsocketCommunicator` (connect → receive latest; broadcast → relay).
- **Frontend** (Vitest + React Testing Library):
  - Reducers/slices (liveRates update, converter computation).
  - WebSocket middleware (dispatch on message, reconnect logic).
  - Components (LiveRatesBoard renders updates, Converter computes, HistoryChart renders data).

## 8. Open Defaults (confirmed)

- Base currency: configurable, default **EUR** (ECB via Frankfurter); cross-rates computed for
  arbitrary pairs.
- Poll interval: `.env`-configurable, default **10s**.
