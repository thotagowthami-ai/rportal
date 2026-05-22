import { test, expect } from "@playwright/test";

test("home page loads", async ({ page }) => {
  const response = await page.goto("/", { waitUntil: "domcontentloaded" });
  expect(response, "home page response").toBeTruthy();
  expect(response && response.ok()).toBeTruthy();

  await expect(page.locator("body")).toBeVisible();
  await expect(page.locator("text=Application error")).toHaveCount(0);
});

test("jobs page loads or redirects without error", async ({ page }) => {
  const response = await page.goto("/jobs", { waitUntil: "domcontentloaded" });
  expect(response, "jobs page response").toBeTruthy();
  expect(response && response.status()).toBeLessThan(400);

  await expect(page.locator("body")).toBeVisible();
  await expect(page.locator("text=Application error")).toHaveCount(0);
});
