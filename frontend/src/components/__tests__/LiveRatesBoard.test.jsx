import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import liveRates, { ratesUpdated } from "../../store/liveRatesSlice";
import LiveRatesBoard from "../LiveRatesBoard";

function renderWithState(fetched_at = null) {
  const store = configureStore({ reducer: { liveRates } });
  store.dispatch(ratesUpdated({ base: "EUR", rates: { EUR: "1.000000", USD: "1.080000" }, fetched_at }));
  render(<Provider store={store}><LiveRatesBoard /></Provider>);
}

describe("LiveRatesBoard", () => {
  it("renders a row per rate", () => {
    renderWithState();
    expect(screen.getByText("USD")).toBeInTheDocument();
    expect(screen.getByText("1.080000")).toBeInTheDocument();
  });

  it("labels the timestamp as the ECB publication, with its date", () => {
    const iso = "2026-10-15T14:00:11Z";
    renderWithState(iso);
    const label = screen.getByText(/ECB rates as of/);
    const day = new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
    expect(label.textContent).toContain(day);
    expect(label.textContent).not.toMatch(/Updated/);
  });
});
