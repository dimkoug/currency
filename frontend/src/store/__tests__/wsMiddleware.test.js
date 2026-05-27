import { describe, it, expect, vi, beforeEach } from "vitest";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../liveRatesSlice";
import { createWsMiddleware, wsConnect } from "../wsMiddleware";

class FakeWS {
  constructor(url) { this.url = url; FakeWS.last = this; }
  send() {}
  close() {}
}

beforeEach(() => {
  vi.stubGlobal("WebSocket", FakeWS);
});

describe("wsMiddleware", () => {
  it("dispatches ratesUpdated when a message arrives", () => {
    const store = configureStore({
      reducer: { liveRates },
      middleware: (getDefault) => getDefault().concat(createWsMiddleware()),
    });
    store.dispatch(wsConnect("ws://test/ws/rates/"));
    FakeWS.last.onmessage({ data: JSON.stringify({ base: "EUR", rates: { USD: "1.08" }, fetched_at: null }) });
    expect(store.getState().liveRates.rates.USD).toBe("1.08");
  });
});
