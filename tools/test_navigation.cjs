// Run against `python3 -m http.server 8766` with Playwright installed:
// NODE_PATH=/tmp/elec-navigation-tests/node_modules node tools/test_navigation.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const fixture = JSON.parse(await fs.readFile('data/questions.json', 'utf8')).slice(0, 3).map((q, i) => ({
      ...q, id: `navigation-test-${i}`, year: 2007, agency: '국가직', number: i + 1,
      answer: { choice: i === 2 ? null : 1, status: 'official' },
    }));
    await page.route('**/data/data.js', route => route.fulfill({
      contentType: 'application/javascript',
      body: `window.QUESTION_BANK = ${JSON.stringify({ questions: fixture, exams: [], taxonomy: { categories: [] } })};`,
    }));
    await page.goto(process.env.ELEC_TEST_URL || 'http://127.0.0.1:8766');
    await page.locator('#order-filter').selectOption('chronological');
    const position = async n => {
      await page.waitForFunction(index => document.querySelector('#practice-progress').textContent === `${index} / 3`, n);
      await page.locator('#practice-panel').waitFor({ state: 'visible' });
      assert.equal(await page.locator('.question-card').getAttribute('data-id'), fixture[n - 1].id);
    };
    const setup = () => page.locator('#setup-panel').waitFor({ state: 'visible' });
    const choose = n => page.locator(`.choice[data-choice="${n}"]`).click();
    const grade = () => page.locator('.grade-single').click();
    const next = () => page.locator('.next-single').click();
    const progress = async () => {
      const downloaded = page.waitForEvent('download');
      await page.locator('#export-progress').click();
      const file = await downloaded;
      return JSON.parse(await fs.readFile(await file.path(), 'utf8')).progress;
    };

    await page.locator('#start-practice').click();
    await position(1);
    assert.equal(await page.locator('.previous-single').isDisabled(), true);
    await choose(2);
    await grade();
    await next();
    await position(2);
    await choose(3);
    await page.locator('.previous-single').click();
    await position(1);
    assert.match(await page.locator('.answer-note').textContent(), /오답입니다/);
    assert.equal(await page.locator('.choice[data-choice="2"]').isDisabled(), true);
    assert.equal(await page.locator('.grade-single').isVisible(), false);
    assert.equal(await page.locator('.next-single').isVisible(), true);
    await page.goForward();
    await position(2);
    assert.match(await page.locator('.choice[data-choice="3"]').getAttribute('class'), /is-selected/);
    await choose(1);
    await grade();
    await next();
    await position(3);
    await page.goBack();
    await position(2);
    assert.match(await page.locator('.answer-note').textContent(), /정답입니다/);
    await page.goBack();
    await position(1);
    await page.goForward();
    await position(2);
    let records = await progress();
    assert.equal(records[fixture[0].id].attempts, 1);
    assert.equal(records[fixture[0].id].wrong, 1);
    assert.equal(records[fixture[1].id].attempts, 1);
    assert.equal(records[fixture[1].id].correct, 1);
    assert.equal(await page.locator('.single-actions').evaluate(el => el.scrollWidth <= el.clientWidth), true);
    await page.screenshot({ path: '/tmp/elec-navigation-tests/previous-question-mobile.png', fullPage: true });

    await next();
    await position(3);
    await choose(2);
    await grade();
    assert.match(await page.locator('.answer-note').textContent(), /정답 미확정/);
    await next();
    await page.locator('#result-panel').waitFor({ state: 'visible' });
    await page.locator('.previous-single').click();
    await position(2);
    assert.equal(await page.locator('#result-panel').isVisible(), false);
    await page.locator('#back-to-setup').click();
    await setup();
    await page.goForward();
    await position(1);
    await page.goBack();
    await setup();

    // A new run permits a fresh attempt and discards the old forward path.
    await page.locator('#start-practice').click();
    await position(1);
    assert.equal(await page.locator('.grade-single').isVisible(), true);
    await choose(1);
    await grade();
    records = await progress();
    assert.equal(records[fixture[0].id].attempts, 2);
    await page.locator('#back-to-setup').click();
    await setup();

    // Batch grading survives Back/Forward and resets for the next run.
    await page.locator('input[name="mode"][value="batch"]').check();
    await page.locator('#batch-size').selectOption('3');
    await page.locator('#start-practice').click();
    await page.locator('#batch-actions').waitFor({ state: 'visible' });
    assert.equal(await page.locator('.previous-single').count(), 0);
    for (const q of fixture) await page.locator(`[data-id="${q.id}"] .choice[data-choice="1"]`).click();
    await page.locator('#grade-batch').click();
    const afterBatch = await progress();
    await page.goBack();
    await setup();
    await page.goForward();
    await page.locator('#batch-actions').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#grade-batch').isDisabled(), true);
    assert.equal(await page.locator('.question-card[data-graded="true"]').count(), 3);
    assert.deepEqual(await progress(), afterBatch);
    await page.locator('#back-to-setup').click();
    await setup();
    await page.locator('#start-practice').click();
    await page.locator('#batch-actions').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#grade-batch').isEnabled(), true);
    assert.equal(await page.locator('.question-card[data-graded="true"]').count(), 0);
    assert.deepEqual(errors, []);
    console.log('PASS: previous button, browser Back/Forward, answers, grading counts, completion, setup, new runs, batch mode and mobile layout.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
