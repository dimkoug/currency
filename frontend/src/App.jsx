import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { wsConnect } from "./store/wsMiddleware";
import LiveRatesBoard from "./components/LiveRatesBoard";
import Converter from "./components/Converter";
import HistoryChart from "./components/HistoryChart";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws/rates/";

export default function App() {
  const dispatch = useDispatch();
  const live = useSelector((s) => Object.keys(s.liveRates.rates).length > 0);

  useEffect(() => {
    dispatch(wsConnect(WS_URL));
  }, [dispatch]);

  return (
    <>
      <header className="site-header">
        <div className="container">
          <div className="inner">
            <a className="brand" href="/">
              <span className="brand__mark">M</span>
              <span className="brand__name">
                Meridian<b>FX</b>
              </span>
            </a>
            <span className="live-pill">
              <span className={live ? "dot" : "dot dot--idle"} />
              {live ? "Live market" : "Connecting"}
            </span>
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="container">
          <p className="eyebrow reveal" style={{ animationDelay: "0.05s" }}>
            Real-time foreign exchange
          </p>
          <h1 className="reveal" style={{ animationDelay: "0.12s" }}>
            Currency, <em>in motion.</em>
          </h1>
          <p className="lead reveal" style={{ animationDelay: "0.2s" }}>
            Institutional-grade exchange rates streamed live to your screen, with
            instant conversion and a window into where every pair has been.
          </p>
        </div>
      </section>

      <main className="container">
        <div className="row g-4">
          <div className="col-lg-5 reveal" style={{ animationDelay: "0.28s" }}>
            <Converter />
          </div>
          <div className="col-lg-7 reveal" style={{ animationDelay: "0.36s" }}>
            <LiveRatesBoard />
          </div>
        </div>
        <div className="row g-4 mt-1">
          <div className="col-12 reveal" style={{ animationDelay: "0.44s" }}>
            <HistoryChart base="EUR" />
          </div>
        </div>
      </main>

      <footer className="site-footer">
        <div className="container d-flex flex-wrap justify-content-between gap-2">
          <span>
            <span className="font-display" style={{ color: "var(--text)" }}>
              Meridian<b style={{ color: "var(--mint)" }}>FX</b>
            </span>{" "}
            — rates via the European Central Bank.
          </span>
          <span>For informational purposes only · not investment advice.</span>
        </div>
      </footer>
    </>
  );
}
