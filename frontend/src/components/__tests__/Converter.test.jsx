import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../../store/liveRatesSlice";
import converter from "../../store/converterSlice";
import Converter from "../Converter";

function renderConverter() {
  const store = configureStore({ reducer: { liveRates, converter } });
  store.dispatch(ratesUpdated({ base: "EUR", rates: { EUR: "1", USD: "1.08", GBP: "0.86" }, fetched_at: null }));
  render(<Provider store={store}><Converter /></Provider>);
}

describe("Converter", () => {
  it("shows a converted result", () => {
    renderConverter();
    // default state: 1 USD -> EUR = 1 * 1/1.08
    expect(screen.getByTestId("result").textContent).toContain((1 / 1.08).toFixed(4));
  });

  it("lets the amount be cleared instead of snapping back to 0", () => {
    renderConverter();
    const input = screen.getByLabelText("amount");
    fireEvent.change(input, { target: { value: "" } });
    expect(input.value).toBe("");
    expect(screen.getByTestId("result").textContent).toBe("—");
  });

  it("converts what is typed after clearing, without a leading zero", () => {
    renderConverter();
    const input = screen.getByLabelText("amount");
    fireEvent.change(input, { target: { value: "" } });
    fireEvent.change(input, { target: { value: "50" } });
    expect(input.value).toBe("50");
    expect(screen.getByTestId("result").textContent).toBe((50 / 1.08).toFixed(4));
  });
});
