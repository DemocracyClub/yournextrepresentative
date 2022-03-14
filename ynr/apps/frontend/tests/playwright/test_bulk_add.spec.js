const { test, expect } = require('@playwright/test');

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:8000/');
});

test('home page header', async ({ page }) => {
	const header = await page.$eval('h1', el => el.innerHTML);
	const locator = page.locator('body > div.header > div.header__hero > div > h1');
	await expect(locator).toContainText('Open candidate information for UK elections');
})
