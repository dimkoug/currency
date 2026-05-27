import { describe, it, expect } from "vitest";
import reducer, { ratesUpdated } from "../liveRatesSlice";

describe("liveRatesSlice", () => {
  it("has empty initial state", () => {
    const state = reducer(undefined, { type: "@@INIT" });
    expect(state).toEqual({ base: null, rates: {}, fetchedAt: null });
  });

  it("stores incoming rate updates", () => {
    const action = ratesUpdated({ base: "EUR", rates: { USD: "1.08" }, fetched_at: "2026-05-27T00:00:00Z" });
    const state = reducer(undefined, action);
    expect(state.base).toBe("EUR");
    expect(state.rates.USD).toBe("1.08");
    expect(state.fetchedAt).toBe("2026-05-27T00:00:00Z");
  });
});
