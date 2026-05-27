#!/usr/bin/env bash
set -e

# --- Detect CPU allocation (cgroup-aware, falls back to host) ---------------
detect_cpus() {
  if [ -r /sys/fs/cgroup/cpu.max ]; then                 # cgroup v2
    read -r quota period < /sys/fs/cgroup/cpu.max
    if [ "$quota" != "max" ] && [ -n "$period" ] && [ "$period" -gt 0 ]; then
      echo $(( (quota + period - 1) / period )); return
    fi
  fi
  if [ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ] && [ -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]; then  # cgroup v1
    q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)
    p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)
    if [ "$q" -gt 0 ] && [ "$p" -gt 0 ]; then echo $(( (q + p - 1) / p )); return; fi
  fi
  nproc 2>/dev/null || echo 1
}

CPUS=$(detect_cpus)
[ "$CPUS" -lt 1 ] && CPUS=1
WORKERS=${UVICORN_WORKERS:-$(( CPUS * 2 ))}
[ "$WORKERS" -lt 2 ] && WORKERS=2
[ "$WORKERS" -gt 12 ] && WORKERS=12

echo "[entrypoint] cgroup CPUs=${CPUS} -> uvicorn --workers ${WORKERS}"

# Migrations are handled by the dedicated one-shot `migrate` service (so that
# multiple backend replicas don't race to migrate).
exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers "$WORKERS"
