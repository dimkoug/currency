import { useSelector } from "react-redux";

export default function LiveRatesBoard() {
  const { base, rates, fetchedAt } = useSelector((s) => s.liveRates);
  const codes = Object.keys(rates).sort();
  return (
    <section>
      <h2>Live Rates {base ? `(base ${base})` : ""}</h2>
      {fetchedAt && <p>Updated: {new Date(fetchedAt).toLocaleTimeString()}</p>}
      <table>
        <thead><tr><th>Currency</th><th>Rate</th></tr></thead>
        <tbody>
          {codes.map((code) => (
            <tr key={code}><td>{code}</td><td>{rates[code]}</td></tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
