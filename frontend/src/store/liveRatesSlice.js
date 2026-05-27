import { createSlice } from "@reduxjs/toolkit";

const initialState = { base: null, rates: {}, fetchedAt: null };

const liveRatesSlice = createSlice({
  name: "liveRates",
  initialState,
  reducers: {
    ratesUpdated(state, action) {
      const { base, rates, fetched_at } = action.payload;
      state.base = base;
      state.rates = rates;
      state.fetchedAt = fetched_at ?? null;
    },
  },
});

export const { ratesUpdated } = liveRatesSlice.actions;
export default liveRatesSlice.reducer;
