import { useSelector } from "react-redux";
import { currencyMeta } from "../lib/currencyMeta";

// fetched_at is when the ECB rate last changed (it publishes once per working
// day), not the last poll — so show the date, e.g. "15 Oct, 17:00".
function formatAsOf(iso) {
  const d = new Date(iso);
  const day = d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
  const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  return `${day}, ${time}`;
}

export default function LiveRatesBoard() {
  const { base, rates, fetchedAt } = useSelector((s) => s.liveRates);
  const quotes = Object.keys(rates)
    .filter((c) => c !== base)
    .sort();

  return (
    <section className="fx-card" aria-label="Live exchange rates">
      <div className="fx-card__head">
        <div>
          <p className="eyebrow mb-0">Markets</p>
          <h2 className="fx-card__title">
            Live rates {base && <span className="rate-base">· 1 {base}</span>}
          </h2>
        </div>
        <span className="fx-card__meta">
          {fetchedAt
            ? `ECB rates as of ${formatAsOf(fetchedAt)}`
            : "Awaiting feed…"}
        </span>
      </div>

      {quotes.length === 0 ? (
        <div className="empty-state">Connecting to the live rate feed…</div>
      ) : (
        <table className="rates-table">
          <thead>
            <tr>
              <th>Currency</th>
              <th className="text-end-col">Rate{base ? ` per ${base}` : ""}</th>
            </tr>
          </thead>
          <tbody>
            {quotes.map((code) => {
              const meta = currencyMeta(code);
              return (
                <tr key={code}>
                  <td>
                    <div className="pair">
                      <span className="pair__flag">{meta.flag}</span>
                      <span>
                        <span className="pair__code">{code}</span>
                        <span className="pair__name d-block">{meta.name}</span>
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className="rate-val">{rates[code]}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
