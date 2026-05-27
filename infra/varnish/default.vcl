vcl 4.1;

# Varnish is now an internal sidecar that only caches the API. nginx (the front
# door) forwards /api/ here; on a miss we fetch from nginx's /_origin_api/ path,
# which load-balances across the backend replicas. Fetching the origin via a
# different path avoids re-entering the cached /api route (no loop).
backend default {
    .host = "frontend";
    .port = "80";
    .connect_timeout = 5s;
    .first_byte_timeout = 60s;
    .between_bytes_timeout = 60s;
}

sub vcl_recv {
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }
    unset req.http.Cookie;
    return (hash);
}

sub vcl_backend_fetch {
    set bereq.url = regsub(bereq.url, "^/api/", "/_origin_api/");
}

sub vcl_backend_response {
    # Micro-cache: absorb spikes, tolerate ~2s staleness; grace serves a slightly
    # stale copy while one request refreshes.
    set beresp.ttl = 2s;
    set beresp.grace = 5s;
    unset beresp.http.Set-Cookie;
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}
