import { test, expect } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL;

if (!baseURL) {
  throw new Error("PLAYWRIGHT_BASE_URL is required for smoke tests");
}

test('@smoke login page loads', async ({ page }) => {
  await page.goto(`${baseURL}/login`);
  await expect(page).toHaveURL(/\/login/);
});

test('@smoke signup page loads', async ({ page }) => {
  await page.goto(`${baseURL}/signup`);
  await expect(page).toHaveURL(/\/signup/);
});
