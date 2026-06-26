import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || process.env.BASE_URL;

if (!baseURL) {
  throw new Error(
    "Set PLAYWRIGHT_BASE_URL or BASE_URL before running Playwright tests.\n" +
    "  Example: PLAYWRIGHT_BASE_URL=https://your-app.railway.app npx playwright test"
  );
}

export default defineConfig({
  testDir: "./tests",

  // Per-test timeout
  timeout: 30_000,

  // Per-expect timeout
  expect: {
    timeout: 7_000,
  },

  // Retry once on CI, never locally
  retries: process.env.CI ? 1 : 0,

  // Run tests in parallel
  fullyParallel: true,
  workers: process.env.CI ? 2 : undefined,

  // Reporters: list for terminal, HTML for review
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],

  use: {
    baseURL,

    // Capture trace on first retry (useful for debugging failures)
    trace: "on-first-retry",

    // Screenshot on failure
    screenshot: "only-on-failure",

    // Video on first retry
    video: "on-first-retry",

    // Reasonable navigation timeout
    navigationTimeout: 20_000,
  },

  projects: [
    // ── Smoke tests (public pages, no auth needed) ──────────────────────────
    {
      name: "smoke-chromium",
      testMatch: "**/smoke.spec.ts",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "smoke-firefox",
      testMatch: "**/smoke.spec.ts",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "smoke-mobile",
      testMatch: "**/smoke.spec.ts",
      use: { ...devices["iPhone 14"] },
    },

    // ── Auth flow tests (requires TEST_EMAIL + TEST_PASSWORD) ───────────────
    {
      name: "auth-chromium",
      testMatch: "**/auth-flows.spec.ts",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
