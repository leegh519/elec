// Run against a local server with Playwright and CHROME_PATH configured.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium', headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.ELEC_TEST_URL || 'http://127.0.0.1:8768');
    assert.equal(await page.locator('#total-count').textContent(), '1,100');
    await page.locator('#category-filter input[value="electronic-circuits"]').check();
    assert.equal(await page.locator('#topic-filter .topic-group-heading').count(), 6);
    assert.equal(await page.locator('#filter-result').textContent(), '563문제');
    assert.match(await page.locator('#topic-filter').textContent(), /증폭도·dB·입출력 임피던스/);
    await page.locator('#reset-filters').click();
    await page.locator('#category-filter input[value="digital-engineering"]').check();
    assert.equal(await page.locator('#topic-filter .topic-group-heading').count(), 4);
    assert.equal(await page.locator('#filter-result').textContent(), '263문제');
    const topicIds = await page.locator('#topic-filter input').evaluateAll(nodes => nodes.map(node => node.value));
    assert.equal(new Set(topicIds).size, topicIds.length);
    for (const topic of topicIds) {
      const box = page.locator(`#topic-filter input[value="${topic}"]`);
      await box.check();
      assert.notEqual(await page.locator('#filter-result').textContent(), '0문제', topic);
      await box.uncheck();
    }
    await page.locator('#topic-filter input[value="memory"]').check();
    assert.equal(await page.locator('#filter-result').textContent(), '2문제');
    await page.locator('#order-filter').selectOption('chronological');
    await page.locator('#start-practice').click();
    assert.equal(await page.locator('.question-card').getAttribute('data-id'), 'national-2021-04');
    await page.locator('.problem-image').evaluate(image => image.decode());
    await page.locator('#back-to-setup').click();
    await page.locator('#reset-filters').click();
    await page.locator('#topic-filter input[value="comparator-schmitt"]').check();
    await page.locator('#topic-filter input[value="pulse-555"]').check();
    assert.equal(await page.locator('#filter-result').textContent(), '23문제');
    await page.locator('#category-filter input[value="digital-engineering"]').check();
    assert.equal(await page.locator('#topic-filter input:checked').count(), 0);
    assert.equal(await page.locator('#filter-result').textContent(), '263문제');
    assert.deepEqual(errors, []);
    console.log('PASS: study groups, topic names, nonempty digital topics, ROM practice, OR union and category switching.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
