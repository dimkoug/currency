import { configureStore } from "@reduxjs/toolkit";
import liveRates from "./liveRatesSlice";
import converter from "./converterSlice";

export const makeStore = (extra = {}) =>
  configureStore({
    reducer: { liveRates, converter, ...extra.reducer },
    middleware: (getDefault) =>
      extra.middleware ? extra.middleware(getDefault) : getDefault(),
  });

export const store = makeStore();
