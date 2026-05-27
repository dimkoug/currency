import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./vitest.setup.js",
    // Unit tests live in src/; e2e/ is Playwright (run separately).
    include: ["src/**/*.{test,spec}.{js,jsx}"],
  },
});
