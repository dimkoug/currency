import { defineConfig, devices } from "@playwright/test";

// Runs against an already-running stack (the front door). In CI the e2e job
// brings the stack up first and sets BASE_URL.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30000,
  expect: { timeout: 20000 },
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:8080",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
