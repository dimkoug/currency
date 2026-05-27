import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
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
});
