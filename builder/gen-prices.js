/* Builds builder/prices.json from the builder's own pricing code (kitDelivered + add-ons),
   so snapinboatcarpets.com can check an "Order now" price before checkout.
   Run: node builder/gen-prices.js   (needs playwright + chromium)
   Runs automatically in GitHub Actions whenever builder/index.html changes. */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const file = path.join(__dirname, 'index.html');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/*', r => (r.request().url().startsWith('file:') ? r.continue() : r.abort()));
  await page.goto('file://' + file + '?skin=snapin');
  await page.waitForTimeout(1500);
  const out = await page.evaluate(() => {
    const prices = {};
    const saved = JSON.stringify({ make: S.make, model: S.model, matType: S.matType, pricePerSY: S.pricePerSY, zip: S.zip });
    const mats = { berber: S_BERBER, vinyl: S_VINYL };
    let count = 0;
    Object.keys(MD).forEach(mk => {
      (MD[mk].m || []).forEach(m => {
        const k = mk + '|' + m;
        const def = SVG_DEFS[k];
        const variants = [{ id: '' }].concat(PATTERN_VARIANTS[k] || []);
        variants.forEach(v => {
          const pcs = (v.pieceDefs && v.pieceDefs.length) ? v.pieceDefs : (def ? def.pieces : null);
          let sf = 0;
          if (pcs) pcs.forEach(p => { sf += p.sf; });
          else ALL.forEach(id => { sf += PIECES[id].sf; });
          const row = {};
          Object.keys(mats).forEach(mt => {
            S.make = mk; S.model = m; S.matType = mt; S.pricePerSY = mats[mt];
            const arr = [];
            for (let d = 0; d <= 9; d++) { S.zip = d + '0000'; arr.push(Math.round(kitDelivered(sf))); }
            row[mt] = arr;
          });
          prices[k + '|' + (v.id || '')] = row;
          count++;
        });
      });
    });
    Object.assign(S, JSON.parse(saved));
    const addons = {};
    Object.keys(ADDONS).forEach(id => { addons[id] = calcAddon(ADDONS[id], {}); });
    const ver = (document.documentElement.innerHTML.match(/v10\.\d+/g) || []).sort((a, b) => parseInt(a.split('.')[1]) - parseInt(b.split('.')[1])).pop();
    return { builder: ver, count, addons, prices };
  });
  await browser.close();
  if (errors.length) console.warn('page errors:', errors.slice(0, 3));
  if (!out.count) { console.error('no prices generated'); process.exit(1); }
  const doc = { builder: out.builder, generated: new Date().toISOString(), note: 'Delivered kit price by ZIP first digit 0-9 (index), full kit, before add-ons. Key: make|model|variant.', addons: out.addons, prices: out.prices };
  fs.writeFileSync(path.join(__dirname, 'prices.json'), JSON.stringify(doc));
  console.log('prices.json:', out.count, 'entries, builder', out.builder);
})();
