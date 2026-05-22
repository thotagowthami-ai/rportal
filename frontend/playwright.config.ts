import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || process.env.BASE_URL;

if (!baseURL) {
  throw new Error("Set PLAYWRIGHT_BASE_URL or BASE_URL before running Playwright tests.");
}

export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  expect: {
    timeout: 7000,
  },
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
