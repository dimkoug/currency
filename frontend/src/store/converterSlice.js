import { createSlice } from "@reduxjs/toolkit";

const initialState = { from: "USD", to: "EUR", amount: 1 };

const converterSlice = createSlice({
  name: "converter",
  initialState,
  reducers: {
    setFrom(state, action) { state.from = action.payload; },
    setTo(state, action) { state.to = action.payload; },
    setAmount(state, action) { state.amount = action.payload; },
  },
});

export const { setFrom, setTo, setAmount } = converterSlice.actions;
export default converterSlice.reducer;
