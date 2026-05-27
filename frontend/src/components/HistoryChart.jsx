import { useState } from "react";
import {
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useGetHistoryQuery } from "../store/api";
import { currencyMeta } from "../lib/currencyMeta";

const QUOTES = ["USD", "GBP", "JPY", "CHF", "AUD", "CAD"];
const MINT = "#34e5a1";

function FxTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="fx-tooltip">
      <div className="t-time">{label}</div>
      <div className="t-val">{payload[0].value}</div>
    </div>
  );
}

export default function HistoryChart({ base = "EUR" }) {
  const [quote, setQuote] = useState("USD");
  const { data = [] } = useGetHistoryQuery({ base, quote });
  const points = data.map((p) => ({
    time: new Date(p.fetched_at).toLocaleTimeString(),
    rate: Number(p.rate),
  }));

  return (
    <section className="fx-card" aria-label="Rate history">
      <div className="fx-card__head">
        <div>
          <p className="eyebrow mb-0">History</p>
          <h2 className="fx-card__title">
            {base} / {quote}{" "}
            <span className="fx-card__meta">{currencyMeta(quote).flag}</span>
          </h2>
        </div>
        <select
          className="cur-select form-select"
          aria-label="history-quote"
          value={quote}
          onChange={(e) => setQuote(e.target.value)}
        >
          {QUOTES.map((c) => (
            <option key={c} value={c}>
              {currencyMeta(c).flag} {c}
            </option>
          ))}
        </select>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={points} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
            <defs>
              <linearGradient id="fxFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={MINT} stopOpacity={0.32} />
                <stop offset="100%" stopColor={MINT} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="time" tickLine={false} axisLine={false} minTickGap={48} />
            <YAxis
              domain={["auto", "auto"]}
              tickLine={false}
              axisLine={false}
              width={56}
            />
            <Tooltip content={<FxTooltip />} cursor={{ stroke: "rgba(255,255,255,0.18)" }} />
            <Area
              type="monotone"
              dataKey="rate"
              stroke={MINT}
              strokeWidth={2.4}
              fill="url(#fxFill)"
              dot={false}
              activeDot={{ r: 4, fill: MINT, stroke: "#04140d", strokeWidth: 2 }}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
