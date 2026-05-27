# Real-Time Currency Exchange Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a containerized app that streams live forex rates over websockets to a React/Redux frontend, with a currency converter and historical charts.

**Architecture:** Django + Channels (ASGI, uvicorn) exposes REST (DRF) + a `/ws/rates/` websocket. Celery Beat polls a free forex API (Frankfurter/ECB) on an interval; the worker persists each snapshot to Postgres and broadcasts the latest rates through a Redis-backed Channels group to all clients. A Vite React + Redux Toolkit frontend consumes the websocket for live updates and REST for initial/historical data, served by nginx which proxies `/api` and `/ws`. Everything is orchestrated by docker-compose and configured from a single root `.env`.

**Tech Stack:** Django 5, Django Channels, channels-redis, Celery, Redis, PostgreSQL, Django REST Framework, django-environ, uvicorn, pytest-django; React 18, Vite, Redux Toolkit, RTK Query, Recharts, Vitest, React Testing Library; Docker, docker-compose, nginx.

**Spec:** `docs/superpowers/specs/2026-05-27-realtime-currency-exchange-design.md`

---

## File Structure

### Backend (`backend/`)
- `manage.py` — Django entrypoint
- `requirements.txt` — pinned deps
- `Dockerfile` — backend image (shared by web/worker/beat)
- `config/settings.py` — settings via django-environ
- `config/urls.py` — HTTP URL routing (admin + `/api/`)
- `config/asgi.py` — ASGI app (HTTP + websocket via Channels)
- `config/celery.py` — Celery app
- `config/__init__.py` — loads Celery app
- `rates/models.py` — `Currency`, `ExchangeRate`
- `rates/fetcher.py` — forex API client (repurposed scraper) + conversion helper
- `rates/tasks.py` — `fetch_rates` Celery task
- `rates/consumers.py` — `RatesConsumer` websocket consumer
- `rates/routing.py` — websocket URL routing
- `rates/serializers.py` — DRF serializers
- `rates/views.py` — DRF API views
- `rates/urls.py` — `/api/` routes
- `rates/services.py` — latest-rates + broadcast helpers (shared by task & consumer)
- `rates/tests/` — pytest tests
- `pytest.ini` — pytest config

### Frontend (`frontend/`)
- `Dockerfile` — multi-stage build → nginx
- `nginx.conf` — serve static + proxy `/api` and `/ws`
- `package.json`, `vite.config.js`, `vitest.setup.js`
- `src/main.jsx`, `src/App.jsx`
- `src/store/store.js` — RTK store
- `src/store/liveRatesSlice.js` — websocket-fed live rates
- `src/store/converterSlice.js` — converter input state
- `src/lib/convert.js` — pure cross-rate conversion
- `src/store/api.js` — RTK Query (currencies, history)
- `src/store/wsMiddleware.js` — websocket middleware
- `src/components/LiveRatesBoard.jsx`
- `src/components/Converter.jsx`
- `src/components/HistoryChart.jsx`
- `src/**/__tests__/*.test.{js,jsx}`

### Root
- `.env`, `.env.sample` — single config source
- `docker-compose.yml` — postgres, redis, backend, celery-worker, celery-beat, frontend

---

## Task 1: Root config & .env

**Files:**
- Create: `.env.sample`, `.env`

- [ ] **Step 1: Write `.env.sample`**

```env
# Django
SECRET_KEY=dev-insecure-change-me
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1,backend
CSRF_TRUSTED_ORIGINS=http://localhost,http://localhost:8080

# Postgres
POSTGRES_DB=currency
POSTGRES_USER=currency
POSTGRES_PASSWORD=currency
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# App
FOREX_API_BASE_URL=https://api.frankfurter.app
BASE_CURRENCY=EUR
POLL_INTERVAL_SECONDS=10
SUPPORTED_CURRENCIES=EUR,USD,GBP,JPY,CHF,AUD,CAD

# Frontend (build/runtime)
VITE_API_URL=/api
VITE_WS_URL=ws://localhost:8080/ws/rates/
```

- [ ] **Step 2: Copy to `.env`**

Run: `cp .env.sample .env` (PowerShell: `Copy-Item .env.sample .env`)
Expected: `.env` exists with identical contents.

- [ ] **Step 3: Commit**

```bash
git add .env.sample
git commit -m "chore: add env sample config"
```
(Do not commit `.env`; add it to `.gitignore` in Task 2.)

---

## Task 2: Backend scaffold & dependencies

**Files:**
- Create: `backend/requirements.txt`, `backend/manage.py`, `backend/config/__init__.py`, `backend/config/settings.py`, `backend/config/urls.py`, `backend/config/asgi.py`, `backend/pytest.ini`, `.gitignore`

- [ ] **Step 1: Write `backend/requirements.txt`**

```
Django==5.1.4
channels==4.2.0
channels-redis==4.2.1
celery==5.4.0
redis==5.2.1
djangorestframework==3.15.2
django-environ==0.11.2
psycopg[binary]==3.2.3
uvicorn[standard]==0.34.0
requests==2.32.3
pytest==8.3.4
pytest-django==4.9.0
pytest-asyncio==0.25.0
```

- [ ] **Step 2: Write `.gitignore` (root)**

```
.env
__pycache__/
*.pyc
.pytest_cache/
node_modules/
frontend/dist/
db.sqlite3
```

- [ ] **Step 3: Write `backend/manage.py`**

```python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write `backend/config/__init__.py`**

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

- [ ] **Step 5: Write `backend/config/settings.py`**

```python
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
# Read root .env when present (mounted/copied at deploy); env vars win in containers.
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "rest_framework",
    "rates",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = None
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="currency"),
        "USER": env("POSTGRES_USER", default="currency"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="currency"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")

# App config
FOREX_API_BASE_URL = env("FOREX_API_BASE_URL", default="https://api.frankfurter.app")
BASE_CURRENCY = env("BASE_CURRENCY", default="EUR")
POLL_INTERVAL_SECONDS = env.int("POLL_INTERVAL_SECONDS", default=10)
SUPPORTED_CURRENCIES = env.list("SUPPORTED_CURRENCIES", default=["EUR", "USD", "GBP"])

REST_FRAMEWORK = {"DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]}

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
```

- [ ] **Step 6: Write `backend/config/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("rates.urls")),
]
```

- [ ] **Step 7: Write `backend/config/asgi.py`**

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from rates.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
```

- [ ] **Step 8: Write `backend/pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = test_*.py
asyncio_mode = auto
```

- [ ] **Step 9: Commit**

```bash
git add backend/ .gitignore
git commit -m "chore: scaffold django backend"
```

---

## Task 3: Models — Currency & ExchangeRate

**Files:**
- Create: `backend/rates/__init__.py`, `backend/rates/apps.py`, `backend/rates/models.py`, `backend/rates/admin.py`, `backend/rates/tests/__init__.py`, `backend/rates/tests/test_models.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_models.py`**

```python
import pytest
from rates.models import Currency, ExchangeRate


@pytest.mark.django_db
def test_currency_str():
    c = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    assert str(c) == "USD"


@pytest.mark.django_db
def test_exchange_rate_roundtrip():
    eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
    usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
    rate = ExchangeRate.objects.create(base=eur, quote=usd, rate="1.0850")
    assert rate.base.code == "EUR"
    assert rate.quote.code == "USD"
    assert str(rate.rate) == "1.0850"
    assert rate.fetched_at is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rates.models'` (or import error).

- [ ] **Step 3: Write `backend/rates/__init__.py`** (empty file)

- [ ] **Step 4: Write `backend/rates/apps.py`**

```python
from django.apps import AppConfig


class RatesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rates"
```

- [ ] **Step 5: Write `backend/rates/models.py`**

```python
from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code


class ExchangeRate(models.Model):
    base = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates_as_base")
    quote = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="rates_as_quote")
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["base", "quote", "fetched_at"]),
            models.Index(fields=["fetched_at"]),
        ]
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"{self.base_id}/{self.quote_id}={self.rate}"
```

- [ ] **Step 6: Write `backend/rates/admin.py`**

```python
from django.contrib import admin
from rates.models import Currency, ExchangeRate

admin.site.register(Currency)
admin.site.register(ExchangeRate)
```

- [ ] **Step 7: Create `backend/rates/tests/__init__.py`** (empty file)

- [ ] **Step 8: Make migrations and run test**

Run: `cd backend && python manage.py makemigrations rates && pytest rates/tests/test_models.py -v`
Expected: migration `0001_initial.py` created; both tests PASS.

- [ ] **Step 9: Commit**

```bash
git add backend/rates/
git commit -m "feat: add Currency and ExchangeRate models"
```

---

## Task 4: Conversion logic (pure cross-rate)

**Files:**
- Create: `backend/rates/fetcher.py` (conversion helper portion), `backend/rates/tests/test_convert.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_convert.py`**

```python
import pytest
from decimal import Decimal
from rates.fetcher import convert


def test_convert_same_currency():
    rates = {"EUR": Decimal("1"), "USD": Decimal("1.08")}
    assert convert("USD", "USD", Decimal("50"), rates) == Decimal("50")


def test_convert_cross_rate():
    # base EUR=1, USD=1.08, GBP=0.86 -> 100 USD to GBP = 100 * 0.86/1.08
    rates = {"EUR": Decimal("1"), "USD": Decimal("1.08"), "GBP": Decimal("0.86")}
    result = convert("USD", "GBP", Decimal("100"), rates)
    assert result == (Decimal("100") * Decimal("0.86") / Decimal("1.08")).quantize(Decimal("0.0001"))


def test_convert_unknown_currency_raises():
    rates = {"EUR": Decimal("1"), "USD": Decimal("1.08")}
    with pytest.raises(KeyError):
        convert("USD", "JPY", Decimal("10"), rates)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_convert.py -v`
Expected: FAIL — `ImportError: cannot import name 'convert'`.

- [ ] **Step 3: Write `backend/rates/fetcher.py` (conversion helper)**

```python
from decimal import Decimal, ROUND_HALF_UP


def convert(from_code: str, to_code: str, amount: Decimal, rates: dict) -> Decimal:
    """Convert amount from `from_code` to `to_code` using base-relative rates.

    `rates` maps currency code -> rate relative to a common base (base itself = 1).
    Raises KeyError if either currency is missing.
    """
    value = amount * (rates[to_code] / rates[from_code])
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest rates/tests/test_convert.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/rates/fetcher.py backend/rates/tests/test_convert.py
git commit -m "feat: add cross-rate conversion helper"
```

---

## Task 5: Forex API fetcher (repurposed scraper)

**Files:**
- Modify: `backend/rates/fetcher.py`
- Create: `backend/rates/tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_fetcher.py`**

```python
from decimal import Decimal
from unittest.mock import patch, MagicMock
from rates.fetcher import fetch_latest_rates


def _mock_response(payload):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


@patch("rates.fetcher.requests.get")
def test_fetch_latest_rates_parses_payload(mock_get):
    mock_get.return_value = _mock_response({
        "amount": 1, "base": "EUR", "date": "2026-05-27",
        "rates": {"USD": 1.08, "GBP": 0.86},
    })
    result = fetch_latest_rates(
        base="EUR",
        symbols=["USD", "GBP"],
        api_base_url="https://api.frankfurter.app",
    )
    assert result.base == "EUR"
    # base is included as 1, quotes are Decimals
    assert result.rates["EUR"] == Decimal("1")
    assert result.rates["USD"] == Decimal("1.08")
    assert result.rates["GBP"] == Decimal("0.86")


@patch("rates.fetcher.requests.get")
def test_fetch_latest_rates_builds_request(mock_get):
    mock_get.return_value = _mock_response(
        {"amount": 1, "base": "EUR", "date": "2026-05-27", "rates": {"USD": 1.08}}
    )
    fetch_latest_rates(base="EUR", symbols=["USD"], api_base_url="https://api.frankfurter.app")
    args, kwargs = mock_get.call_args
    assert args[0] == "https://api.frankfurter.app/latest"
    assert kwargs["params"] == {"from": "EUR", "to": "USD"}
    assert kwargs["timeout"] == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_fetcher.py -v`
Expected: FAIL — `ImportError: cannot import name 'fetch_latest_rates'`.

- [ ] **Step 3: Add to `backend/rates/fetcher.py`**

```python
from dataclasses import dataclass
import requests


@dataclass
class RateSnapshot:
    base: str
    rates: dict  # code -> Decimal (includes base = Decimal("1"))
    date: str


def fetch_latest_rates(base: str, symbols: list, api_base_url: str) -> RateSnapshot:
    """Fetch latest rates from a Frankfurter-compatible API.

    Returns a RateSnapshot whose `rates` includes the base currency as Decimal('1').
    """
    quotes = [s for s in symbols if s != base]
    resp = requests.get(
        f"{api_base_url}/latest",
        params={"from": base, "to": ",".join(quotes)},
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()
    rates = {base: Decimal("1")}
    for code, value in payload["rates"].items():
        rates[code] = Decimal(str(value))
    return RateSnapshot(base=base, rates=rates, date=payload["date"])
```

(Place these imports/definitions in the same file as `convert`; keep the existing `from decimal import ...` line, adding `requests` and `dataclass` imports at the top.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest rates/tests/test_fetcher.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/rates/fetcher.py backend/rates/tests/test_fetcher.py
git commit -m "feat: add forex API fetcher"
```

---

## Task 6: Services — persist & broadcast helpers

**Files:**
- Create: `backend/rates/services.py`, `backend/rates/tests/test_services.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_services.py`**

```python
import pytest
from decimal import Decimal
from rates.fetcher import RateSnapshot
from rates.models import Currency, ExchangeRate
from rates.services import save_snapshot, latest_rates_payload


@pytest.mark.django_db
def test_save_snapshot_creates_currencies_and_rates():
    snap = RateSnapshot(
        base="EUR",
        rates={"EUR": Decimal("1"), "USD": Decimal("1.08"), "GBP": Decimal("0.86")},
        date="2026-05-27",
    )
    save_snapshot(snap)
    assert Currency.objects.filter(code="USD").exists()
    # base->quote rows for every non-base currency
    assert ExchangeRate.objects.filter(base__code="EUR", quote__code="USD").count() == 1
    assert ExchangeRate.objects.filter(base__code="EUR", quote__code="GBP").count() == 1


@pytest.mark.django_db
def test_latest_rates_payload_returns_most_recent():
    snap = RateSnapshot(base="EUR", rates={"EUR": Decimal("1"), "USD": Decimal("1.08")}, date="2026-05-27")
    save_snapshot(snap)
    payload = latest_rates_payload()
    assert payload["base"] == "EUR"
    assert payload["rates"]["USD"] == "1.080000"
    assert payload["rates"]["EUR"] == "1.000000"
    assert "fetched_at" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_services.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rates.services'`.

- [ ] **Step 3: Write `backend/rates/services.py`**

```python
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rates.models import Currency, ExchangeRate

RATES_GROUP = "rates"


def save_snapshot(snapshot):
    """Persist a RateSnapshot: ensure Currency rows, insert base->quote ExchangeRate rows."""
    base, _ = Currency.objects.get_or_create(
        code=snapshot.base, defaults={"name": snapshot.base}
    )
    new_rows = []
    for code, value in snapshot.rates.items():
        quote, _ = Currency.objects.get_or_create(code=code, defaults={"name": code})
        if code == snapshot.base:
            continue
        new_rows.append(ExchangeRate(base=base, quote=quote, rate=value))
    ExchangeRate.objects.bulk_create(new_rows)


def latest_rates_payload():
    """Build the latest-rates payload (base currency + code->rate string + timestamp)."""
    base_code = settings.BASE_CURRENCY
    latest = (
        ExchangeRate.objects.filter(base__code=base_code)
        .order_by("quote_id", "-fetched_at")
        .distinct("quote_id")
    )
    rates = {base_code: "1.000000"}
    fetched_at = None
    for row in latest:
        rates[row.quote_id] = str(row.rate)
        if fetched_at is None or row.fetched_at > fetched_at:
            fetched_at = row.fetched_at
    return {
        "base": base_code,
        "rates": rates,
        "fetched_at": fetched_at.isoformat() if fetched_at else None,
    }


def broadcast_latest():
    """Send the latest-rates payload to the Channels group."""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        RATES_GROUP, {"type": "rates.update", "payload": latest_rates_payload()}
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest rates/tests/test_services.py -v`
Expected: PASS (2 tests). Note: `.distinct("quote_id")` requires PostgreSQL — run tests against Postgres (see Task 14 test note).

- [ ] **Step 5: Commit**

```bash
git add backend/rates/services.py backend/rates/tests/test_services.py
git commit -m "feat: add snapshot persistence and broadcast helpers"
```

---

## Task 7: Celery app & fetch_rates task

**Files:**
- Create: `backend/config/celery.py`, `backend/rates/tasks.py`, `backend/rates/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_tasks.py`**

```python
import pytest
from decimal import Decimal
from unittest.mock import patch
from rates.fetcher import RateSnapshot
from rates.models import ExchangeRate


@pytest.mark.django_db
@patch("rates.tasks.broadcast_latest")
@patch("rates.tasks.fetch_latest_rates")
def test_fetch_rates_task_persists_and_broadcasts(mock_fetch, mock_broadcast):
    from rates.tasks import fetch_rates
    mock_fetch.return_value = RateSnapshot(
        base="EUR", rates={"EUR": Decimal("1"), "USD": Decimal("1.08")}, date="2026-05-27"
    )
    fetch_rates()
    assert ExchangeRate.objects.filter(base__code="EUR", quote__code="USD").count() == 1
    mock_broadcast.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_tasks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rates.tasks'`.

- [ ] **Step 3: Write `backend/config/celery.py`**

```python
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("currency")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Register the periodic forex poll directly on the beat schedule. Referencing the
# task by name avoids importing rates.tasks at module load (circular import), and
# setting beat_schedule explicitly is more reliable than the on_after_configure signal.
app.conf.beat_schedule = {
    "poll-forex-rates": {
        "task": "rates.tasks.fetch_rates",
        "schedule": float(settings.POLL_INTERVAL_SECONDS),
    }
}
```

> **Note (integration fix):** An earlier version used the `@app.on_after_configure.connect` signal with `add_periodic_task`. That signal did not fire in the `celery beat` process, so no task was scheduled. Setting `app.conf.beat_schedule` directly is the reliable pattern. Also note all three backend-based services (`backend`, `celery-worker`, `celery-beat`) build separate images — rebuild ALL of them after changing backend code.

- [ ] **Step 4: Write `backend/rates/tasks.py`**

```python
from celery import shared_task
from django.conf import settings
from rates.fetcher import fetch_latest_rates
from rates.services import save_snapshot, broadcast_latest


@shared_task
def fetch_rates():
    """Poll the forex API, persist a snapshot, and broadcast the latest rates."""
    snapshot = fetch_latest_rates(
        base=settings.BASE_CURRENCY,
        symbols=settings.SUPPORTED_CURRENCIES,
        api_base_url=settings.FOREX_API_BASE_URL,
    )
    save_snapshot(snapshot)
    broadcast_latest()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest rates/tests/test_tasks.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/config/celery.py backend/rates/tasks.py backend/rates/tests/test_tasks.py
git commit -m "feat: add celery app and fetch_rates task"
```

---

## Task 8: Websocket consumer & routing

**Files:**
- Create: `backend/rates/consumers.py`, `backend/rates/routing.py`, `backend/rates/tests/test_consumer.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_consumer.py`**

```python
import pytest
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from config.asgi import application
from rates.services import RATES_GROUP


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_consumer_receives_broadcast():
    communicator = WebsocketCommunicator(application, "/ws/rates/")
    connected, _ = await communicator.connect()
    assert connected

    layer = get_channel_layer()
    await layer.group_send(
        RATES_GROUP,
        {"type": "rates.update", "payload": {"base": "EUR", "rates": {"USD": "1.08"}}},
    )
    message = await communicator.receive_json_from(timeout=2)
    assert message["base"] == "EUR"
    assert message["rates"]["USD"] == "1.08"
    await communicator.disconnect()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_consumer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rates.routing'` (import in asgi.py) / consumer missing.

- [ ] **Step 3: Write `backend/rates/consumers.py`**

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from rates.services import RATES_GROUP, latest_rates_payload


class RatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(RATES_GROUP, self.channel_name)
        await self.accept()
        payload = await sync_to_async(latest_rates_payload)()
        await self.send_json(payload)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(RATES_GROUP, self.channel_name)

    async def rates_update(self, event):
        await self.send_json(event["payload"])
```

- [ ] **Step 4: Write `backend/rates/routing.py`**

```python
from django.urls import path
from rates.consumers import RatesConsumer

websocket_urlpatterns = [
    path("ws/rates/", RatesConsumer.as_asgi()),
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest rates/tests/test_consumer.py -v`
Expected: PASS. (Requires Redis running for the channel layer, or set an in-memory layer in test settings — see Task 14 note.)

- [ ] **Step 6: Commit**

```bash
git add backend/rates/consumers.py backend/rates/routing.py backend/rates/tests/test_consumer.py
git commit -m "feat: add rates websocket consumer"
```

---

## Task 9: REST API — serializers, views, urls

**Files:**
- Create: `backend/rates/serializers.py`, `backend/rates/views.py`, `backend/rates/urls.py`, `backend/rates/tests/test_api.py`

- [ ] **Step 1: Write the failing test — `backend/rates/tests/test_api.py`**

```python
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rates.fetcher import RateSnapshot
from rates.services import save_snapshot
from rates.models import Currency


@pytest.fixture
def seeded(db):
    save_snapshot(RateSnapshot(
        base="EUR",
        rates={"EUR": Decimal("1"), "USD": Decimal("1.08"), "GBP": Decimal("0.86")},
        date="2026-05-27",
    ))


def test_currencies_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/currencies/")
    assert resp.status_code == 200
    codes = {c["code"] for c in resp.json()}
    assert {"EUR", "USD", "GBP"} <= codes


def test_latest_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/rates/latest/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["base"] == "EUR"
    assert body["rates"]["USD"] == "1.080000"


def test_history_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/rates/history/?base=EUR&quote=USD")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) >= 1
    assert "rate" in points[0] and "fetched_at" in points[0]


def test_convert_endpoint(seeded):
    client = APIClient()
    resp = client.get("/api/convert/?from=USD&to=GBP&amount=100")
    assert resp.status_code == 200
    body = resp.json()
    expected = (Decimal("100") * Decimal("0.86") / Decimal("1.08")).quantize(Decimal("0.0001"))
    assert body["result"] == str(expected)


def test_convert_unknown_currency_returns_400(seeded):
    client = APIClient()
    resp = client.get("/api/convert/?from=USD&to=JPY&amount=100")
    assert resp.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest rates/tests/test_api.py -v`
Expected: FAIL — URLs / views not found (404 or import error).

- [ ] **Step 3: Write `backend/rates/serializers.py`**

```python
from rest_framework import serializers
from rates.models import Currency, ExchangeRate


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["code", "name", "symbol"]


class HistoryPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ["rate", "fetched_at"]
```

- [ ] **Step 4: Write `backend/rates/views.py`**

```python
from decimal import Decimal, InvalidOperation
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rates.models import Currency, ExchangeRate
from rates.serializers import CurrencySerializer, HistoryPointSerializer
from rates.services import latest_rates_payload
from rates.fetcher import convert


class CurrencyListView(ListAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class LatestRatesView(APIView):
    def get(self, request):
        return Response(latest_rates_payload())


class HistoryView(ListAPIView):
    serializer_class = HistoryPointSerializer

    def get_queryset(self):
        base = self.request.query_params.get("base", settings.BASE_CURRENCY)
        quote = self.request.query_params.get("quote")
        qs = ExchangeRate.objects.filter(base__code=base)
        if quote:
            qs = qs.filter(quote__code=quote)
        return qs.order_by("fetched_at")[:500]


class ConvertView(APIView):
    def get(self, request):
        from_code = request.query_params.get("from")
        to_code = request.query_params.get("to")
        try:
            amount = Decimal(request.query_params.get("amount", "0"))
        except InvalidOperation:
            return Response({"error": "invalid amount"}, status=400)
        payload = latest_rates_payload()
        rates = {k: Decimal(v) for k, v in payload["rates"].items()}
        try:
            result = convert(from_code, to_code, amount, rates)
        except KeyError:
            return Response({"error": "unknown currency"}, status=400)
        return Response({"from": from_code, "to": to_code, "amount": str(amount), "result": str(result)})
```

- [ ] **Step 5: Write `backend/rates/urls.py`**

```python
from django.urls import path
from rates.views import CurrencyListView, LatestRatesView, HistoryView, ConvertView

urlpatterns = [
    path("currencies/", CurrencyListView.as_view()),
    path("rates/latest/", LatestRatesView.as_view()),
    path("rates/history/", HistoryView.as_view()),
    path("convert/", ConvertView.as_view()),
]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pytest rates/tests/test_api.py -v`
Expected: PASS (5 tests).

- [ ] **Step 7: Run the full backend suite**

Run: `cd backend && pytest -v`
Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/rates/serializers.py backend/rates/views.py backend/rates/urls.py backend/rates/tests/test_api.py
git commit -m "feat: add REST API for currencies, rates, history, convert"
```

---

## Task 10: Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`, `backend/entrypoint.sh`

- [ ] **Step 1: Write `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
```

- [ ] **Step 2: Write `backend/entrypoint.sh`**

```bash
#!/usr/bin/env bash
set -e
python manage.py migrate --noinput
exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

- [ ] **Step 3: Commit**

```bash
git add backend/Dockerfile backend/entrypoint.sh
git commit -m "chore: add backend Dockerfile and entrypoint"
```

---

## Task 11: docker-compose orchestration

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    env_file: .env
    depends_on:
      postgres: {condition: service_healthy}
      redis: {condition: service_healthy}
    expose:
      - "8000"

  celery-worker:
    build: ./backend
    command: celery -A config worker -l info
    env_file: .env
    depends_on:
      - backend
      - redis

  celery-beat:
    build: ./backend
    command: celery -A config beat -l info
    env_file: .env
    depends_on:
      - backend
      - redis

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: ${VITE_API_URL}
        VITE_WS_URL: ${VITE_WS_URL}
    ports:
      - "8080:80"
    depends_on:
      - backend

volumes:
  pgdata:
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add docker-compose orchestration"
```

---

## Task 12: Frontend scaffold & store

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.js`, `frontend/vitest.setup.js`, `frontend/index.html`, `frontend/src/main.jsx`, `frontend/src/store/store.js`

- [ ] **Step 1: Write `frontend/package.json`**

```json
{
  "name": "currency-frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "@reduxjs/toolkit": "^2.3.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-redux": "^9.1.2",
    "recharts": "^2.13.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.1",
    "@vitejs/plugin-react": "^4.3.3",
    "jsdom": "^25.0.1",
    "vite": "^5.4.10",
    "vitest": "^2.1.4"
  }
}
```

- [ ] **Step 2: Write `frontend/vite.config.js`**

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./vitest.setup.js",
  },
});
```

- [ ] **Step 3: Write `frontend/vitest.setup.js`**

```javascript
import "@testing-library/jest-dom";
```

- [ ] **Step 4: Write `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Currency Exchange</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Write `frontend/src/store/store.js`** (api/middleware added in later tasks)

```javascript
import { configureStore } from "@reduxjs/toolkit";
import liveRates from "./liveRatesSlice";
import converter from "./converterSlice";

export const makeStore = (extra = {}) =>
  configureStore({
    reducer: { liveRates, converter, ...extra.reducer },
    middleware: (getDefault) =>
      extra.middleware ? extra.middleware(getDefault) : getDefault(),
  });

export const store = makeStore();
```

- [ ] **Step 6: Write `frontend/src/main.jsx`**

```javascript
import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { store } from "./store/store";
import App from "./App";

createRoot(document.getElementById("root")).render(
  <Provider store={store}>
    <App />
  </Provider>
);
```

- [ ] **Step 7: Install deps**

Run: `cd frontend && npm install`
Expected: `node_modules/` populated, no errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/package.json frontend/vite.config.js frontend/vitest.setup.js frontend/index.html frontend/src/main.jsx frontend/src/store/store.js
git commit -m "chore: scaffold vite react frontend"
```

---

## Task 13: liveRates slice

**Files:**
- Create: `frontend/src/store/liveRatesSlice.js`, `frontend/src/store/__tests__/liveRatesSlice.test.js`

- [ ] **Step 1: Write the failing test — `frontend/src/store/__tests__/liveRatesSlice.test.js`**

```javascript
import { describe, it, expect } from "vitest";
import reducer, { ratesUpdated } from "../liveRatesSlice";

describe("liveRatesSlice", () => {
  it("has empty initial state", () => {
    const state = reducer(undefined, { type: "@@INIT" });
    expect(state).toEqual({ base: null, rates: {}, fetchedAt: null });
  });

  it("stores incoming rate updates", () => {
    const action = ratesUpdated({ base: "EUR", rates: { USD: "1.08" }, fetched_at: "2026-05-27T00:00:00Z" });
    const state = reducer(undefined, action);
    expect(state.base).toBe("EUR");
    expect(state.rates.USD).toBe("1.08");
    expect(state.fetchedAt).toBe("2026-05-27T00:00:00Z");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- liveRatesSlice`
Expected: FAIL — cannot resolve `../liveRatesSlice`.

- [ ] **Step 3: Write `frontend/src/store/liveRatesSlice.js`**

```javascript
import { createSlice } from "@reduxjs/toolkit";

const initialState = { base: null, rates: {}, fetchedAt: null };

const liveRatesSlice = createSlice({
  name: "liveRates",
  initialState,
  reducers: {
    ratesUpdated(state, action) {
      const { base, rates, fetched_at } = action.payload;
      state.base = base;
      state.rates = rates;
      state.fetchedAt = fetched_at ?? null;
    },
  },
});

export const { ratesUpdated } = liveRatesSlice.actions;
export default liveRatesSlice.reducer;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- liveRatesSlice`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/store/liveRatesSlice.js frontend/src/store/__tests__/liveRatesSlice.test.js
git commit -m "feat: add liveRates slice"
```

---

## Task 14: Pure conversion + converter slice

**Files:**
- Create: `frontend/src/lib/convert.js`, `frontend/src/lib/__tests__/convert.test.js`, `frontend/src/store/converterSlice.js`, `frontend/src/store/__tests__/converterSlice.test.js`

- [ ] **Step 1: Write the failing test — `frontend/src/lib/__tests__/convert.test.js`**

```javascript
import { describe, it, expect } from "vitest";
import { convert } from "../convert";

describe("convert", () => {
  it("returns same amount for same currency", () => {
    expect(convert("USD", "USD", 50, { EUR: "1", USD: "1.08" })).toBeCloseTo(50, 4);
  });

  it("computes cross rate", () => {
    const result = convert("USD", "GBP", 100, { EUR: "1", USD: "1.08", GBP: "0.86" });
    expect(result).toBeCloseTo((100 * 0.86) / 1.08, 4);
  });

  it("returns null when a currency is missing", () => {
    expect(convert("USD", "JPY", 100, { EUR: "1", USD: "1.08" })).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- convert`
Expected: FAIL — cannot resolve `../convert`.

- [ ] **Step 3: Write `frontend/src/lib/convert.js`**

```javascript
export function convert(from, to, amount, rates) {
  const fromRate = rates[from];
  const toRate = rates[to];
  if (fromRate == null || toRate == null) return null;
  return (Number(amount) * Number(toRate)) / Number(fromRate);
}
```

- [ ] **Step 4: Run convert test to verify it passes**

Run: `cd frontend && npm test -- convert`
Expected: PASS (3 tests).

- [ ] **Step 5: Write the failing test — `frontend/src/store/__tests__/converterSlice.test.js`**

```javascript
import { describe, it, expect } from "vitest";
import reducer, { setFrom, setTo, setAmount } from "../converterSlice";

describe("converterSlice", () => {
  it("has default state", () => {
    const state = reducer(undefined, { type: "@@INIT" });
    expect(state).toEqual({ from: "USD", to: "EUR", amount: 1 });
  });

  it("updates fields", () => {
    let state = reducer(undefined, setFrom("GBP"));
    state = reducer(state, setTo("JPY"));
    state = reducer(state, setAmount(250));
    expect(state).toEqual({ from: "GBP", to: "JPY", amount: 250 });
  });
});
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd frontend && npm test -- converterSlice`
Expected: FAIL — cannot resolve `../converterSlice`.

- [ ] **Step 7: Write `frontend/src/store/converterSlice.js`**

```javascript
import { createSlice } from "@reduxjs/toolkit";

const initialState = { from: "USD", to: "EUR", amount: 1 };

const converterSlice = createSlice({
  name: "converter",
  initialState,
  reducers: {
    setFrom(state, action) { state.from = action.payload; },
    setTo(state, action) { state.to = action.payload; },
    setAmount(state, action) { state.amount = action.payload; },
  },
});

export const { setFrom, setTo, setAmount } = converterSlice.actions;
export default converterSlice.reducer;
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd frontend && npm test -- converterSlice`
Expected: PASS (2 tests).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/lib/ frontend/src/store/converterSlice.js frontend/src/store/__tests__/converterSlice.test.js
git commit -m "feat: add conversion helper and converter slice"
```

---

## Task 15: RTK Query API & websocket middleware

**Files:**
- Create: `frontend/src/store/api.js`, `frontend/src/store/wsMiddleware.js`, `frontend/src/store/__tests__/wsMiddleware.test.js`
- Modify: `frontend/src/store/store.js`

- [ ] **Step 1: Write `frontend/src/store/api.js`**

```javascript
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const API_URL = import.meta.env.VITE_API_URL || "/api";

export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: API_URL }),
  endpoints: (builder) => ({
    getCurrencies: builder.query({ query: () => "/currencies/" }),
    getHistory: builder.query({
      query: ({ base, quote }) => `/rates/history/?base=${base}&quote=${quote}`,
    }),
  }),
});

export const { useGetCurrenciesQuery, useGetHistoryQuery } = api;
```

- [ ] **Step 2: Write the failing test — `frontend/src/store/__tests__/wsMiddleware.test.js`**

```javascript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../liveRatesSlice";
import { createWsMiddleware, wsConnect } from "../wsMiddleware";

class FakeWS {
  constructor(url) { this.url = url; FakeWS.last = this; }
  send() {}
  close() {}
}

beforeEach(() => {
  vi.stubGlobal("WebSocket", FakeWS);
});

describe("wsMiddleware", () => {
  it("dispatches ratesUpdated when a message arrives", () => {
    const store = configureStore({
      reducer: { liveRates },
      middleware: (getDefault) => getDefault().concat(createWsMiddleware()),
    });
    store.dispatch(wsConnect("ws://test/ws/rates/"));
    FakeWS.last.onmessage({ data: JSON.stringify({ base: "EUR", rates: { USD: "1.08" }, fetched_at: null }) });
    expect(store.getState().liveRates.rates.USD).toBe("1.08");
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd frontend && npm test -- wsMiddleware`
Expected: FAIL — cannot resolve `../wsMiddleware`.

- [ ] **Step 4: Write `frontend/src/store/wsMiddleware.js`**

```javascript
import { ratesUpdated } from "./liveRatesSlice";

export const wsConnect = (url) => ({ type: "ws/connect", payload: url });

export function createWsMiddleware() {
  return (storeApi) => {
    let socket = null;
    let retry = 1000;

    const connect = (url) => {
      socket = new WebSocket(url);
      socket.onmessage = (event) => {
        storeApi.dispatch(ratesUpdated(JSON.parse(event.data)));
      };
      socket.onopen = () => { retry = 1000; };
      socket.onclose = () => {
        setTimeout(() => connect(url), retry);
        retry = Math.min(retry * 2, 30000);
      };
    };

    return (next) => (action) => {
      if (action.type === "ws/connect") {
        if (socket) socket.close();
        connect(action.payload);
        return;
      }
      return next(action);
    };
  };
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npm test -- wsMiddleware`
Expected: PASS.

- [ ] **Step 6: Update `frontend/src/store/store.js` to wire api + middleware**

```javascript
import { configureStore } from "@reduxjs/toolkit";
import liveRates from "./liveRatesSlice";
import converter from "./converterSlice";
import { api } from "./api";
import { createWsMiddleware } from "./wsMiddleware";

export const store = configureStore({
  reducer: {
    liveRates,
    converter,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefault) =>
    getDefault().concat(api.middleware, createWsMiddleware()),
});
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/store/api.js frontend/src/store/wsMiddleware.js frontend/src/store/__tests__/wsMiddleware.test.js frontend/src/store/store.js
git commit -m "feat: add RTK Query api and websocket middleware"
```

---

## Task 16: Components — LiveRatesBoard, Converter, HistoryChart, App

**Files:**
- Create: `frontend/src/components/LiveRatesBoard.jsx`, `frontend/src/components/Converter.jsx`, `frontend/src/components/HistoryChart.jsx`, `frontend/src/App.jsx`, `frontend/src/components/__tests__/Converter.test.jsx`, `frontend/src/components/__tests__/LiveRatesBoard.test.jsx`

- [ ] **Step 1: Write the failing test — `frontend/src/components/__tests__/LiveRatesBoard.test.jsx`**

```javascript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../../store/liveRatesSlice";
import LiveRatesBoard from "../LiveRatesBoard";

function renderWithState() {
  const store = configureStore({ reducer: { liveRates } });
  store.dispatch(ratesUpdated({ base: "EUR", rates: { EUR: "1.000000", USD: "1.080000" }, fetched_at: null }));
  render(<Provider store={store}><LiveRatesBoard /></Provider>);
}

describe("LiveRatesBoard", () => {
  it("renders a row per rate", () => {
    renderWithState();
    expect(screen.getByText("USD")).toBeInTheDocument();
    expect(screen.getByText("1.080000")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- LiveRatesBoard`
Expected: FAIL — cannot resolve `../LiveRatesBoard`.

- [ ] **Step 3: Write `frontend/src/components/LiveRatesBoard.jsx`**

```javascript
import { useSelector } from "react-redux";

export default function LiveRatesBoard() {
  const { base, rates, fetchedAt } = useSelector((s) => s.liveRates);
  const codes = Object.keys(rates).sort();
  return (
    <section>
      <h2>Live Rates {base ? `(base ${base})` : ""}</h2>
      {fetchedAt && <p>Updated: {new Date(fetchedAt).toLocaleTimeString()}</p>}
      <table>
        <thead><tr><th>Currency</th><th>Rate</th></tr></thead>
        <tbody>
          {codes.map((code) => (
            <tr key={code}><td>{code}</td><td>{rates[code]}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- LiveRatesBoard`
Expected: PASS.

- [ ] **Step 5: Write the failing test — `frontend/src/components/__tests__/Converter.test.jsx`**

```javascript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../../store/liveRatesSlice";
import converter from "../../store/converterSlice";
import Converter from "../Converter";

function renderConverter() {
  const store = configureStore({ reducer: { liveRates, converter } });
  store.dispatch(ratesUpdated({ base: "EUR", rates: { EUR: "1", USD: "1.08", GBP: "0.86" }, fetched_at: null }));
  render(<Provider store={store}><Converter /></Provider>);
}

describe("Converter", () => {
  it("shows a converted result", () => {
    renderConverter();
    // default state: 1 USD -> EUR = 1 * 1/1.08
    expect(screen.getByTestId("result").textContent).toContain((1 / 1.08).toFixed(4));
  });
});
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd frontend && npm test -- Converter`
Expected: FAIL — cannot resolve `../Converter`.

- [ ] **Step 7: Write `frontend/src/components/Converter.jsx`**

```javascript
import { useSelector, useDispatch } from "react-redux";
import { setFrom, setTo, setAmount } from "../store/converterSlice";
import { convert } from "../lib/convert";

export default function Converter() {
  const dispatch = useDispatch();
  const rates = useSelector((s) => s.liveRates.rates);
  const { from, to, amount } = useSelector((s) => s.converter);
  const codes = Object.keys(rates).sort();
  const result = convert(from, to, amount, rates);

  return (
    <section>
      <h2>Converter</h2>
      <input
        type="number"
        aria-label="amount"
        value={amount}
        onChange={(e) => dispatch(setAmount(Number(e.target.value)))}
      />
      <select aria-label="from" value={from} onChange={(e) => dispatch(setFrom(e.target.value))}>
        {codes.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      <select aria-label="to" value={to} onChange={(e) => dispatch(setTo(e.target.value))}>
        {codes.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      <span data-testid="result">{result == null ? "—" : result.toFixed(4)}</span>
    </section>
  );
}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd frontend && npm test -- Converter`
Expected: PASS.

- [ ] **Step 9: Write `frontend/src/components/HistoryChart.jsx`**

```javascript
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useGetHistoryQuery } from "../store/api";

export default function HistoryChart({ base = "EUR" }) {
  const [quote, setQuote] = useState("USD");
  const { data = [] } = useGetHistoryQuery({ base, quote });
  const points = data.map((p) => ({
    time: new Date(p.fetched_at).toLocaleTimeString(),
    rate: Number(p.rate),
  }));

  return (
    <section>
      <h2>History {base}/{quote}</h2>
      <select aria-label="history-quote" value={quote} onChange={(e) => setQuote(e.target.value)}>
        {["USD", "GBP", "JPY", "CHF", "AUD", "CAD"].map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={points}>
          <XAxis dataKey="time" />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey="rate" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
```

- [ ] **Step 10: Write `frontend/src/App.jsx`**

```javascript
import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { wsConnect } from "./store/wsMiddleware";
import LiveRatesBoard from "./components/LiveRatesBoard";
import Converter from "./components/Converter";
import HistoryChart from "./components/HistoryChart";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws/rates/";

export default function App() {
  const dispatch = useDispatch();
  useEffect(() => {
    dispatch(wsConnect(WS_URL));
  }, [dispatch]);

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 800, margin: "0 auto", padding: 16 }}>
      <h1>Real-Time Currency Exchange</h1>
      <Converter />
      <LiveRatesBoard />
      <HistoryChart base="EUR" />
    </main>
  );
}
```

- [ ] **Step 11: Run the full frontend suite**

Run: `cd frontend && npm test`
Expected: all tests PASS.

- [ ] **Step 12: Commit**

```bash
git add frontend/src/components/ frontend/src/App.jsx
git commit -m "feat: add live rates board, converter, history chart, and app shell"
```

---

## Task 17: Frontend Dockerfile & nginx

**Files:**
- Create: `frontend/Dockerfile`, `frontend/nginx.conf`

- [ ] **Step 1: Write `frontend/nginx.conf`**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

- [ ] **Step 2: Write `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_URL
ARG VITE_WS_URL
ENV VITE_API_URL=$VITE_API_URL VITE_WS_URL=$VITE_WS_URL
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

- [ ] **Step 3: Commit**

```bash
git add frontend/Dockerfile frontend/nginx.conf
git commit -m "chore: add frontend Dockerfile and nginx config"
```

---

## Task 18: Integration smoke test

**Files:** none (verification only)

- [ ] **Step 1: Build and start the stack**

Run: `docker compose up --build -d`
Expected: all six services start; `docker compose ps` shows postgres & redis healthy.

- [ ] **Step 2: Verify REST API**

Run: `curl http://localhost:8080/api/currencies/`
Expected: after the first poll (~10s), JSON list including EUR/USD/GBP. Re-run if empty.

- [ ] **Step 3: Verify latest rates**

Run: `curl http://localhost:8080/api/rates/latest/`
Expected: JSON with `base: "EUR"` and a populated `rates` object.

- [ ] **Step 4: Verify the websocket pushes updates**

Open `http://localhost:8080` in a browser. Expected: Live Rates table populates and the "Updated" timestamp changes roughly every `POLL_INTERVAL_SECONDS`; the converter shows a result; the history chart renders after a few polls.

- [ ] **Step 5: Verify Celery Beat is polling**

Run: `docker compose logs celery-beat | tail -n 20` and `docker compose logs celery-worker | tail -n 20`
Expected: beat logs "Scheduler: Sending due task poll-forex-rates"; worker logs successful `fetch_rates` runs.

- [ ] **Step 6: Tear down**

Run: `docker compose down`
Expected: containers stopped and removed.

- [ ] **Step 7: Commit any fixes**

```bash
git add -A
git commit -m "chore: integration fixes from smoke test"
```

---

## Notes for the implementing engineer

- **Test database & PostgreSQL features:** `latest_rates_payload` uses `.distinct("quote_id")`, which is PostgreSQL-only. Run the backend test suite against Postgres (e.g. `POSTGRES_HOST=localhost` with a local Postgres, or `docker compose run --rm backend pytest`). Do not switch the test DB to SQLite.
- **Channel layer in tests:** The consumer test needs a working channel layer. Either run Redis locally during tests, or add a pytest fixture/`settings` override setting `CHANNEL_LAYERS` to `channels.layers.InMemoryChannelLayer` for that test module. If you use the in-memory layer, keep the `transaction=True` marker.
- **`asgiref` / `channels` versions:** `AsyncJsonWebsocketConsumer` and `WebsocketCommunicator` come from the pinned `channels==4.2.0`. Don't upgrade mid-implementation.
- **First-load empty state:** Until the first poll completes, `/api/rates/latest/` returns `rates: {"EUR": "1.000000"}` only and the websocket sends the same. The frontend must handle an empty/near-empty rates object gracefully (the components above already do).
- **`.env` in containers:** `env_file: .env` injects vars into each container's environment; `django-environ` reads them from the environment (the `read_env` call is a no-op fallback for local non-container runs).
