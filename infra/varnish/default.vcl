vcl 4.1;

# Upstream is the nginx (frontend) container, which serves the SPA and reverse
# proxies /api and /ws to the Django backend.
backend default {
    .host = "frontend";
    .port = "80";
    .connect_timeout = 5s;
    .first_byte_timeout = 60s;
    .between_bytes_timeout = 60s;
}

sub vcl_recv {
    # WebSockets cannot be cached or buffered -> pipe straight through.
    if (req.http.Upgrade ~ "(?i)websocket") {
        return (pipe);
    }

    # Only GET/HEAD are cacheable.
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # The SPA shell must always revalidate (so new build hashes are picked up).
    if (req.url == "/" || req.url ~ "^/index\.html") {
        return (pass);
    }

    # Cacheable surfaces: hashed build assets (immutable) and the read-only API
    # (micro-cached). Drop cookies so they don't fragment/bypass the cache.
    if (req.url ~ "^/assets/" || req.url ~ "^/api/") {
        unset req.http.Cookie;
        return (hash);
    }

    # Everything else (client-side routes, favicon, etc.) -> straight to nginx.
    return (pass);
}

sub vcl_pipe {
    # Preserve the upgrade handshake when piping websockets.
    if (req.http.Upgrade) {
        set bereq.http.Upgrade = req.http.Upgrade;
        set bereq.http.Connection = "Upgrade";
    }
}

sub vcl_backend_response {
    if (bereq.url ~ "^/assets/") {
        set beresp.ttl = 365d;
        set beresp.http.Cache-Control = "public, max-age=31536000, immutable";
        unset beresp.http.Set-Cookie;
        return (deliver);
    }
    if (bereq.url ~ "^/api/") {
        # Micro-cache: absorb load spikes, tolerate up to ~2s staleness. Grace
        # lets one request refresh while others are served the slightly-stale copy.
        set beresp.ttl = 2s;
        set beresp.grace = 5s;
        unset beresp.http.Set-Cookie;
        return (deliver);
    }
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}
