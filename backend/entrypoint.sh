#!/usr/bin/env bash
set -e

# --- Detect CPU allocation (cgroup-aware, falls back to host) ---------------
detect_cpus() {
  if [ -r /sys/fs/cgroup/cpu.max ]; then
    # cgroup v2: "<quota> <period>"; "max" means unlimited
    read -r quota period < /sys/fs/cgroup/cpu.max
    if [ "$quota" != "max" ] && [ -n "$period" ] && [ "$period" -gt 0 ]; then
      echo $(( (quota + period - 1) / period ))
      return
    fi
  fi
  if [ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ] && [ -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]; then
    q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)
    p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)
    if [ "$q" -gt 0 ] && [ "$p" -gt 0 ]; then
      echo $(( (q + p - 1) / p ))
      return
    fi
  fi
  nproc 2>/dev/null || echo 1
}

CPUS=$(detect_cpus)
[ "$CPUS" -lt 1 ] && CPUS=1

# Each uvicorn worker is a full event loop. We run ~2x CPUs because connect-time
# work includes a blocking DB call dispatched to a thread pool; extra workers
# spread that load. Override with UVICORN_WORKERS.
WORKERS=${UVICORN_WORKERS:-$(( CPUS * 2 ))}
[ "$WORKERS" -lt 2 ] && WORKERS=2
[ "$WORKERS" -gt 12 ] && WORKERS=12

echo "[entrypoint] cgroup CPUs=${CPUS} -> uvicorn --workers ${WORKERS}"

# Run migrations against Postgres DIRECTLY (not through pgbouncer): transaction
# pooling is a poor fit for migration DDL / session state.
echo "[entrypoint] running migrations (direct to ${MIGRATE_DB_HOST:-postgres}:${MIGRATE_DB_PORT:-5432})"
POSTGRES_HOST="${MIGRATE_DB_HOST:-postgres}" POSTGRES_PORT="${MIGRATE_DB_PORT:-5432}" \
  python manage.py migrate --noinput

exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers "$WORKERS"
