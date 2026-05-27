FROM postgres:16

COPY tune.sh /usr/local/bin/tune.sh
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/tune.sh /usr/local/bin/start.sh

# Wrap the stock entrypoint so we inject resource-derived tuning flags at boot.
ENTRYPOINT ["/usr/local/bin/start.sh"]
