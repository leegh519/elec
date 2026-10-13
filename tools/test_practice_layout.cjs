// NODE_PATH=<Playwright modules> node tools/test_practice_layout.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
  });
  try {
    const questions = JSON.parse(await fs.readFile('data/questions.json', 'utf8'));
    const tall = [...questions].sort((a, b) => b.image.height / b.image.width - a.image.height / a.image.width)[0];
    const fixture = [4, 5].map((choiceCount, i) => ({
      ...tall, id: `layout-test-${i}`, number: i + 1, choiceCount,
      classification: { category: '', concepts: ['회로'.repeat(30), '긴 분류명'.repeat(20)] },
      answer: { choice: 1, status: 'official' },
    }));
    for (const [width, height] of [[1440, 900], [1280, 720], [1024, 600], [375, 812], [390, 600], [844, 390]]) {
      const page = await browser.newPage({ viewport: { width, height } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/data/data.js', route => route.fulfill({
        contentType: 'application/javascript',
        body: `window.QUESTION_BANK = ${JSON.stringify({ questions: fixture, exams: [], taxonomy: { categories: [] } })};`,
      }));
      await page.goto(process.env.ELEC_TEST_URL || pathToFileURL(path.resolve('index.html')).href);
      await page.locator('#order-filter').selectOption('chronological');
      await page.locator('#start-practice').click();
      const fits = async () => {
        await page.locator('.problem-image').evaluate(img => img.decode());
        const layout = await page.evaluate(() => {
          const card = document.querySelector('.question-card');
          const image = document.querySelector('.problem-image');
          const answer = document.querySelector('.answer-area').getBoundingClientRect();
          const main = document.querySelector('main').getBoundingClientRect();
          const header = document.querySelector('.site-header').getBoundingClientRect();
          return {
            documentFits: document.documentElement.scrollHeight <= innerHeight + 1,
            widthFits: document.documentElement.scrollWidth <= innerWidth + 1,
            cardFits: card.scrollHeight <= card.clientHeight + 1,
            answerFits: answer.bottom <= innerHeight && answer.top >= 0,
            sidebar: header.right <= main.left,
            imageVisible: image.getBoundingClientRect().height > 20,
          };
        });
        for (const [check, passed] of Object.entries(layout)) assert.equal(passed, true, `${width}x${height}: ${check}`);
      };
      await fits();
      await page.locator('#toggle-all-meta').click();
      await fits();
      await page.locator('.choice[data-choice="2"]').click();
      await page.locator('.grade-single').click();
      await fits();
      await page.locator('.next-single').click();
      assert.equal(await page.locator('.choice').count(), 5);
      await fits();
      await page.goBack();
      assert.equal(await page.locator('.question-card').getAttribute('data-id'), fixture[0].id);
      await fits();
      if (width === 1280) await page.screenshot({ path: '/tmp/elec-practice-desktop.png' });
      if (width === 375) await page.screenshot({ path: '/tmp/elec-practice-mobile.png' });
      await page.locator('#back-to-setup').click();
      await page.locator('#setup-panel').waitFor({ state: 'visible' });
      assert.equal(await page.locator('body').evaluate(el => el.classList.contains('practice-active')), false);
      assert.equal(await page.locator('body > .site-header').count(), 1);
      await page.locator('input[value="batch"]').check();
      await page.locator('#start-practice').click();
      assert.equal(await page.locator('#practice-sidebar #batch-actions').count(), 1);
      assert.equal(await page.locator('#question-list').evaluate(el => getComputedStyle(el).overflowY), 'auto');
      assert.deepEqual(errors, []);
      await page.close();
      console.log(`PASS ${width}x${height}: image, answer, metadata, grading, five choices, navigation, setup and batch.`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
