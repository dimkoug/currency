import { useSelector } from "react-redux";
import { currencyMeta } from "../lib/currencyMeta";

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
            ? `Updated ${new Date(fetchedAt).toLocaleTimeString()}`
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
