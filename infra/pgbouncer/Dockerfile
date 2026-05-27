FROM alpine:3.20

RUN apk add --no-cache pgbouncer su-exec \
 && (addgroup -S pgbouncer 2>/dev/null || true) \
 && (adduser -S -D -H -G pgbouncer pgbouncer 2>/dev/null || true)

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 6432
ENTRYPOINT ["/start.sh"]
