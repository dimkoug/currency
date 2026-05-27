import { useSelector, useDispatch } from "react-redux";
import { setFrom, setTo, setAmount } from "../store/converterSlice";
import { convert } from "../lib/convert";
import { currencyMeta } from "../lib/currencyMeta";

export default function Converter() {
  const dispatch = useDispatch();
  const rates = useSelector((s) => s.liveRates.rates);
  const { from, to, amount } = useSelector((s) => s.converter);
  const codes = Object.keys(rates).sort();
  const result = convert(from, to, amount, rates);
  const unit = convert(from, to, 1, rates);

  const swap = () => {
    dispatch(setFrom(to));
    dispatch(setTo(from));
  };

  const options = codes.map((c) => (
    <option key={c} value={c}>
      {currencyMeta(c).flag} {c}
    </option>
  ));

  return (
    <section className="fx-card" aria-label="Currency converter">
      <div className="fx-card__head">
        <div>
          <p className="eyebrow mb-0">Convert</p>
          <h2 className="fx-card__title">Exchange desk</h2>
        </div>
      </div>

      <div className="conv-field">
        <div className="conv-field__label">You send</div>
        <div className="row-line">
          <input
            type="number"
            className="conv-amount"
            aria-label="amount"
            value={amount}
            min="0"
            onChange={(e) => dispatch(setAmount(Number(e.target.value)))}
          />
          <select
            className="cur-select form-select"
            aria-label="from"
            value={from}
            onChange={(e) => dispatch(setFrom(e.target.value))}
          >
            {options}
          </select>
        </div>
      </div>

      <div className="swap-row">
        <button type="button" className="swap-btn" onClick={swap} aria-label="Swap currencies">
          ⇅
        </button>
      </div>

      <div className="conv-field">
        <div className="conv-field__label">They receive</div>
        <div className="row-line">
          <span className="conv-result" data-testid="result">
            {result == null ? "—" : result.toFixed(4)}
          </span>
          <select
            className="cur-select form-select"
            aria-label="to"
            value={to}
            onChange={(e) => dispatch(setTo(e.target.value))}
          >
            {options}
          </select>
        </div>
      </div>

      <div className="conv-rate-line">
        {unit == null ? (
          "Awaiting live rates…"
        ) : (
          <>
            1 <b>{from}</b> = {unit.toFixed(4)} <b>{to}</b>
          </>
        )}
      </div>
    </section>
  );
}
