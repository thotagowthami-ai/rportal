import { test, expect } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'https://recruit-app-v1-5itoz54is-ven010s-projects.vercel.app';

test('@smoke login page loads', async ({ page }) => {
  await page.goto(`${baseURL}/login`);
  await expect(page).toHaveURL(/\/login/);
});

test('@smoke signup page loads', async ({ page }) => {
  await page.goto(`${baseURL}/signup`);
  await expect(page).toHaveURL(/\/signup/);
});
