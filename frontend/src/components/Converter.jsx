import { useSelector, useDispatch } from "react-redux";
import { setFrom, setTo, setAmount } from "../store/converterSlice";
import { convert } from "../lib/convert";

export default function Converter() {
  const dispatch = useDispatch();
  const rates = useSelector((s) => s.liveRates.rates);
  const { from, to, amount } = useSelector((s) => s.converter);
  const codes = Object.keys(rates).sort();
  const result = convert(from, to, amount, rates);

  return (
    <section>
      <h2>Converter</h2>
      <input
        type="number"
        aria-label="amount"
        value={amount}
        onChange={(e) => dispatch(setAmount(Number(e.target.value)))}
      />
      <select aria-label="from" value={from} onChange={(e) => dispatch(setFrom(e.target.value))}>
        {codes.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      <select aria-label="to" value={to} onChange={(e) => dispatch(setTo(e.target.value))}>
        {codes.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      <span data-testid="result">{result == null ? "—" : result.toFixed(4)}</span>
    </section>
  );
}
