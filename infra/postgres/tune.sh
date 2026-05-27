#!/usr/bin/env bash
# Print Postgres tuning flags (`-c key=val ...`) computed from the container's
# cgroup-allocated RAM and CPU. Falls back to host totals if unconstrained.
set -e

detect_mem_bytes() {
  if [ -r /sys/fs/cgroup/memory.max ]; then            # cgroup v2
    v=$(cat /sys/fs/cgroup/memory.max)
    [ "$v" != "max" ] && echo "$v" && return
  fi
  if [ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then  # cgroup v1
    v=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
    # very large value == effectively unlimited
    if [ "$v" -lt 9000000000000000 ]; then echo "$v"; return; fi
  fi
  awk '/MemTotal/ {print $2 * 1024}' /proc/meminfo
}

detect_cpus() {
  if [ -r /sys/fs/cgroup/cpu.max ]; then                 # cgroup v2
    read -r q p < /sys/fs/cgroup/cpu.max
    if [ "$q" != "max" ] && [ -n "$p" ] && [ "$p" -gt 0 ]; then
      echo $(( (q + p - 1) / p )); return
    fi
  fi
  if [ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ] && [ -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]; then  # cgroup v1
    q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us)
    p=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us)
    if [ "$q" -gt 0 ] && [ "$p" -gt 0 ]; then echo $(( (q + p - 1) / p )); return; fi
  fi
  nproc 2>/dev/null || echo 1
}

MEM_MB=$(( $(detect_mem_bytes) / 1024 / 1024 ))
CPUS=$(detect_cpus); [ "$CPUS" -lt 1 ] && CPUS=1

SHARED=$(( MEM_MB / 4 ))                 # 25% RAM
EFFCACHE=$(( MEM_MB * 3 / 4 ))           # 75% RAM
MAINT=$(( MEM_MB / 16 )); [ "$MAINT" -gt 512 ] && MAINT=512
WORKMEM=$(( MEM_MB / 256 )); [ "$WORKMEM" -lt 4 ] && WORKMEM=4
PARALLEL=$(( CPUS / 2 )); [ "$PARALLEL" -lt 1 ] && PARALLEL=1

>&2 echo "[pg-tune] mem=${MEM_MB}MB cpus=${CPUS} -> shared_buffers=${SHARED}MB effective_cache_size=${EFFCACHE}MB work_mem=${WORKMEM}MB"

echo "-c shared_buffers=${SHARED}MB \
-c effective_cache_size=${EFFCACHE}MB \
-c maintenance_work_mem=${MAINT}MB \
-c work_mem=${WORKMEM}MB \
-c max_connections=${PG_MAX_CONNECTIONS:-200} \
-c max_worker_processes=${CPUS} \
-c max_parallel_workers=${CPUS} \
-c max_parallel_workers_per_gather=${PARALLEL} \
-c effective_io_concurrency=200 \
-c random_page_cost=1.1 \
-c wal_compression=on"
