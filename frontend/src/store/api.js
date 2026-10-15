import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const API_URL = import.meta.env.VITE_API_URL || "/api";

// The history chart shows one point per day over this window (API max: 90).
export const HISTORY_DAYS = 90;

export const historyQuery = ({ base, quote }) =>
  `/rates/history/?base=${base}&quote=${quote}&days=${HISTORY_DAYS}`;

export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: API_URL }),
  endpoints: (builder) => ({
    getCurrencies: builder.query({ query: () => "/currencies/" }),
    getHistory: builder.query({ query: historyQuery }),
  }),
});

export const { useGetCurrenciesQuery, useGetHistoryQuery } = api;
