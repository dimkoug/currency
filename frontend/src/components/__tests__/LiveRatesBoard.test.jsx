import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../../store/liveRatesSlice";
import LiveRatesBoard from "../LiveRatesBoard";

function renderWithState() {
  const store = configureStore({ reducer: { liveRates } });
  store.dispatch(ratesUpdated({ base: "EUR", rates: { EUR: "1.000000", USD: "1.080000" }, fetched_at: null }));
  render(<Provider store={store}><LiveRatesBoard /></Provider>);
}

describe("LiveRatesBoard", () => {
  it("renders a row per rate", () => {
    renderWithState();
    expect(screen.getByText("USD")).toBeInTheDocument();
    expect(screen.getByText("1.080000")).toBeInTheDocument();
  });
});
