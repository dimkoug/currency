import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { wsConnect } from "./store/wsMiddleware";
import LiveRatesBoard from "./components/LiveRatesBoard";
import Converter from "./components/Converter";
import HistoryChart from "./components/HistoryChart";

// Derive the websocket URL from the page's own origin so it always routes
// through the same nginx that served the app (which proxies /ws to the backend),
// regardless of which host/port the site is served on. This avoids brittle
// build-time hardcoding of host:port.
const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/rates/`;

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
