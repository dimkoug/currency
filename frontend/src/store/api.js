import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const API_URL = import.meta.env.VITE_API_URL || "/api";

export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: API_URL }),
  endpoints: (builder) => ({
    getCurrencies: builder.query({ query: () => "/currencies/" }),
    getHistory: builder.query({
      query: ({ base, quote }) => `/rates/history/?base=${base}&quote=${quote}`,
    }),
  }),
});

export const { useGetCurrenciesQuery, useGetHistoryQuery } = api;
