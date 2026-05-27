#!/bin/sh
# Generate pgbouncer config + userlist from env, then run in the foreground.
set -e

: "${DB_HOST:=postgres}"
: "${DB_PORT:=5432}"
: "${DB_USER:=currency}"
: "${DB_PASSWORD:=currency}"
: "${LISTEN_PORT:=6432}"
: "${POOL_MODE:=transaction}"
: "${MAX_CLIENT_CONN:=2000}"
: "${DEFAULT_POOL_SIZE:=25}"
: "${MIN_POOL_SIZE:=5}"
: "${RESERVE_POOL_SIZE:=5}"

mkdir -p /etc/pgbouncer

# Plaintext entry is valid for scram-sha-256: pgbouncer derives the exchange for
# both the client side and the server (Postgres) side from it.
printf '"%s" "%s"\n' "$DB_USER" "$DB_PASSWORD" > /etc/pgbouncer/userlist.txt

cat > /etc/pgbouncer/pgbouncer.ini <<EOF
[databases]
* = host=${DB_HOST} port=${DB_PORT}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = ${LISTEN_PORT}
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = ${POOL_MODE}
max_client_conn = ${MAX_CLIENT_CONN}
default_pool_size = ${DEFAULT_POOL_SIZE}
min_pool_size = ${MIN_POOL_SIZE}
reserve_pool_size = ${RESERVE_POOL_SIZE}
ignore_startup_parameters = extra_float_digits,options
admin_users = ${DB_USER}
EOF

chown -R pgbouncer:pgbouncer /etc/pgbouncer

echo "[pgbouncer] ${POOL_MODE} pool -> ${DB_HOST}:${DB_PORT}, listen :${LISTEN_PORT}, default_pool_size=${DEFAULT_POOL_SIZE}, max_client_conn=${MAX_CLIENT_CONN}"
# pgbouncer refuses to run as root; drop privileges to the pgbouncer user.
exec su-exec pgbouncer pgbouncer /etc/pgbouncer/pgbouncer.ini
