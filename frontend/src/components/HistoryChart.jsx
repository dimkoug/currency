import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useGetHistoryQuery } from "../store/api";

export default function HistoryChart({ base = "EUR" }) {
  const [quote, setQuote] = useState("USD");
  const { data = [] } = useGetHistoryQuery({ base, quote });
  const points = data.map((p) => ({
    time: new Date(p.fetched_at).toLocaleTimeString(),
    rate: Number(p.rate),
  }));

  return (
    <section>
      <h2>History {base}/{quote}</h2>
      <select aria-label="history-quote" value={quote} onChange={(e) => setQuote(e.target.value)}>
        {["USD", "GBP", "JPY", "CHF", "AUD", "CAD"].map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={points}>
          <XAxis dataKey="time" />
          <YAxis domain={["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey="rate" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
