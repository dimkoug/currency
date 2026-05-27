import { test, expect } from "@playwright/test";

test("live rates board populates from the websocket", async ({ page }) => {
  await page.goto("/");

  // App shell renders
  await expect(page.getByRole("heading", { name: /Currency, in motion/i })).toBeVisible();

  // The "Live market" pill turns on once the websocket delivers rates
  await expect(page.getByText("Live market")).toBeVisible();

  // Scope assertions to the live-rates board to avoid matching currency codes
  // elsewhere (e.g. converter dropdowns).
  const board = page.getByRole("region", { name: "Live exchange rates" });
  await expect(board.getByText("USD", { exact: true })).toBeVisible();
  // ...with a numeric rate value (6-decimal string from the backend)
  await expect(board.getByText(/^\d+\.\d{6}$/).first()).toBeVisible();
});

test("converter computes a result from live rates", async ({ page }) => {
  await page.goto("/");
  // Wait for rates so the converter has data, then assert the result is numeric.
  await expect(page.getByText("Live market")).toBeVisible();
  const result = page.getByTestId("result");
  await expect(result).toBeVisible();
  await expect(result).toHaveText(/^\d+\.\d{4}$/);
});
