import { describe, it, expect } from "vitest";
import { convert } from "../convert";

describe("convert", () => {
  it("returns same amount for same currency", () => {
    expect(convert("USD", "USD", 50, { EUR: "1", USD: "1.08" })).toBeCloseTo(50, 4);
  });

  it("computes cross rate", () => {
    const result = convert("USD", "GBP", 100, { EUR: "1", USD: "1.08", GBP: "0.86" });
    expect(result).toBeCloseTo((100 * 0.86) / 1.08, 4);
  });

  it("returns null when a currency is missing", () => {
    expect(convert("USD", "JPY", 100, { EUR: "1", USD: "1.08" })).toBeNull();
  });
});
