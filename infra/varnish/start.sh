#!/bin/sh
# Size the Varnish malloc cache from the container's cgroup RAM allocation
# (~75%), then run varnishd in the foreground.
set -e

detect_mem_bytes() {
  if [ -r /sys/fs/cgroup/memory.max ]; then
    v=$(cat /sys/fs/cgroup/memory.max)
    [ "$v" != "max" ] && echo "$v" && return
  fi
  if [ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then
    v=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
    if [ "$v" -lt 9000000000000000 ]; then echo "$v"; return; fi
  fi
  awk '/MemTotal/ {print $2 * 1024}' /proc/meminfo
}

MEM_MB=$(( $(detect_mem_bytes) / 1024 / 1024 ))
SIZE=$(( MEM_MB * 75 / 100 ))
[ "$SIZE" -lt 64 ] && SIZE=64

echo "[varnish] cgroup mem=${MEM_MB}MB -> malloc cache=${SIZE}MB"
exec varnishd -F -a http=:80 -f /etc/varnish/default.vcl -s malloc,${SIZE}m -p feature=+http2
