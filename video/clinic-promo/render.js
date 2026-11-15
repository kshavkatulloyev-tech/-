// Usage:
//   node render.js frames <outDir> [fps]      -> renders every frame as JPEG
//   node render.js stills <outDir> t1 t2 ...  -> renders still frames at given seconds
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const [mode, outDir, ...rest] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForLoadState('networkidle');
  const shot = (file) => page.screenshot({ path: file, type: 'jpeg', quality: 92 });

  if (mode === 'stills') {
    for (const s of rest) {
      const t = parseFloat(s);
      await page.evaluate((t) => window.render(t), t);
      await shot(path.join(outDir, `t_${t.toFixed(2)}.jpg`));
    }
  } else {
    const fps = parseInt(rest[0] || '30', 10);
    const dur = await page.evaluate(() => window.DURATION);
    const n = Math.round(dur * fps);
    for (let f = 0; f < n; f++) {
      await page.evaluate((t) => window.render(t), f / fps);
      await shot(path.join(outDir, `f_${String(f).padStart(5, '0')}.jpg`));
      if (f % 150 === 0) console.log(`frame ${f}/${n}`);
    }
  }
  await browser.close();
})();
