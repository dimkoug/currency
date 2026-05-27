import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { wsConnect } from "./store/wsMiddleware";
import LiveRatesBoard from "./components/LiveRatesBoard";
import Converter from "./components/Converter";
import HistoryChart from "./components/HistoryChart";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws/rates/";

export default function App() {
  const dispatch = useDispatch();
  useEffect(() => {
    dispatch(wsConnect(WS_URL));
  }, [dispatch]);

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 800, margin: "0 auto", padding: 16 }}>
      <h1>Real-Time Currency Exchange</h1>
      <Converter />
      <LiveRatesBoard />
      <HistoryChart base="EUR" />
    </main>
  );
}
