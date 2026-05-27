// End-to-end smoke test for the assembled stack (Varnish → nginx → backend →
// pgbouncer → Postgres, plus the Redis-backed websocket broadcast).
//
// Dependency-free: uses Node's global fetch + WebSocket (Node 22+). Point it at
// the running front door:
//
//   BASE_URL=http://localhost:8080 node e2e/smoke.mjs
//
// Exits non-zero if any check fails.

const BASE = (process.env.BASE_URL || "http://localhost:8080").replace(/\/$/, "");
const WS_URL = BASE.replace(/^http/, "ws") + "/ws/rates/";

let failures = 0;
const check = (name, ok, extra = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${extra ? "  — " + extra : ""}`);
  if (!ok) failures++;
};

// 1. REST API is reachable and rates are populated.
const res = await fetch(`${BASE}/api/rates/latest/`);
const body = await res.json().catch(() => ({}));
check("GET /api/rates/latest/ -> 200", res.status === 200, `status ${res.status}`);
check("rates populated (USD present)", !!(body.rates && body.rates.USD), `USD=${body.rates?.USD}`);
check("base currency is EUR", body.base === "EUR");

// 2. Varnish micro-cache produces a HIT (a few rapid hits within the 2s TTL).
let cacheHit = false;
for (let i = 0; i < 6; i++) {
  const r = await fetch(`${BASE}/api/rates/latest/`);
  if ((r.headers.get("x-cache") || "").toUpperCase() === "HIT") { cacheHit = true; break; }
}
check("Varnish returns an X-Cache: HIT on /api", cacheHit);

// 3. Conversion endpoint works through the stack.
const cv = await fetch(`${BASE}/api/convert/?from=USD&to=GBP&amount=100`);
const cj = await cv.json().catch(() => ({}));
check("GET /api/convert/ -> 200 with result", cv.status === 200 && !!cj.result, `result=${cj.result}`);

// 4. Websocket: initial snapshot + at least one live broadcast (10s poll).
await new Promise((resolve) => {
  let count = 0;
  let baseSeen = null;
  const ws = new WebSocket(WS_URL);
  const done = (ok) => { check("websocket delivers a live broadcast (>=2 msgs)", ok, `received ${count}`); try { ws.close(); } catch {} resolve(); };
  const timer = setTimeout(() => done(count >= 2), 15000);
  ws.onmessage = (e) => {
    count++;
    try { baseSeen = JSON.parse(e.data).base; } catch {}
    if (count >= 2) { clearTimeout(timer); check("websocket base currency is EUR", baseSeen === "EUR"); done(true); }
  };
  ws.onerror = () => { clearTimeout(timer); check("websocket connects", false); resolve(); };
});

console.log(failures ? `\n${failures} check(s) failed` : "\nAll smoke checks passed");
process.exit(failures ? 1 : 0);
