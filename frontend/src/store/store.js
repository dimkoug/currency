import { configureStore } from "@reduxjs/toolkit";
import liveRates from "./liveRatesSlice";
import converter from "./converterSlice";
import { api } from "./api";
import { createWsMiddleware } from "./wsMiddleware";

export const store = configureStore({
  reducer: {
    liveRates,
    converter,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefault) =>
    getDefault().concat(api.middleware, createWsMiddleware()),
});
