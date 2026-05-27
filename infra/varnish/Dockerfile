FROM varnish:7.6

COPY default.vcl /etc/varnish/default.vcl
COPY start.sh /usr/local/bin/start.sh

USER root
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 80
ENTRYPOINT ["/usr/local/bin/start.sh"]
