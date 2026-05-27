import { describe, it, expect } from "vitest";
import reducer, { setFrom, setTo, setAmount } from "../converterSlice";

describe("converterSlice", () => {
  it("has default state", () => {
    const state = reducer(undefined, { type: "@@INIT" });
    expect(state).toEqual({ from: "USD", to: "EUR", amount: 1 });
  });

  it("updates fields", () => {
    let state = reducer(undefined, setFrom("GBP"));
    state = reducer(state, setTo("JPY"));
    state = reducer(state, setAmount(250));
    expect(state).toEqual({ from: "GBP", to: "JPY", amount: 250 });
  });
});
