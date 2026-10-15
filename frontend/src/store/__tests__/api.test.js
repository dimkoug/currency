import { describe, it, expect } from "vitest";
import { historyQuery, HISTORY_DAYS } from "../api";

describe("historyQuery", () => {
  it("requests the last 90 days of daily history for the pair", () => {
    expect(HISTORY_DAYS).toBe(90);
    expect(historyQuery({ base: "EUR", quote: "USD" })).toBe(
      "/rates/history/?base=EUR&quote=USD&days=90"
    );
  });
});
